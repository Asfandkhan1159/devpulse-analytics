from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timezone
from app.db.database import SessionLocal
import httpx
from app.models.events import SyncJob
from app.config import Settings
from app.services.metrics_services import calculate_cutoff
from app.services.normalizers.factory import normalize_event
from app.services.webhook_service import save_event
base_Url_github ="https://api.github.com" 

settings= Settings()

def create_sync_job(project_id,provider,status,db:Session):
    syncJob =SyncJob(
        project_id=project_id,
        provider=provider,
        status=status,
        created_at=datetime.utcnow(),


    )
    db.add(syncJob)
    db.commit()
    db.refresh(syncJob)

    return syncJob

def get_job_status(sync_job_id: int,db:Session):
   status = db.execute(
       select(SyncJob).filter_by(
           id = sync_job_id,
       )
   ).scalar_one_or_none()

   return status

async def call_github_api(client:httpx.AsyncClient, owner:str, repo:str, token:str,cutoff:datetime) -> dict:
    
    headers={
        "Authorization":f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    }

    response = await client.get(f"{base_Url_github}/repos/{owner}/{repo}/actions/runs", headers=headers, 
                                params={
                                    "per_page":100,
                                    "created":f"{cutoff.strftime('%Y-%m-%d')}..{datetime.utcnow().strftime('%Y-%m-%d')}"
                                })

    response.raise_for_status()
    return response.json()

async def call_github_prs_api(client:httpx.AsyncClient, owner:str, repo:str, token:str, cutoff:datetime) ->dict:
    headers={
        "Authorization":f"Bearer {token}",
        "Accept":"application/vnd.github+json",
        "X-Github-APi-Version":"2022-11-28"
    }
    pull_requests = []
    page = 1

    while True:
        response = await client.get(
            f"{base_Url_github}/repos/{owner}/{repo}/pulls",
            headers=headers,
            params={
                "state":"all",
                "per_page":100,
                "page":page,
                "sort":"updated",
                "direction":"desc"
            }
        )
        response.raise_for_status()
        data= response.json()

        if not data:
            break
        for pr in data:
            pr_updated_at = datetime.strptime(pr["updated_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if pr_updated_at >= cutoff:
                pull_requests.append(pr)
            else:
                return pull_requests
        if len(data) < 100:
            break
        page +=1
    return pull_requests            


async def fetch_historical_data(
    sync_job_id: int,
    project_id: int,
    owner: str,
    repo_name: str,
    provider: str,
    access_token: str,
):
    try:
        db = SessionLocal()
        start_job = get_job_status(sync_job_id, db)
        start_job.status = "in_progress"
        db.commit()
        
        cutoff = calculate_cutoff(90)
        async with httpx.AsyncClient() as client:
            data = await call_github_api(client, owner=owner, repo=repo_name, token=access_token, cutoff=cutoff)
            prs_data = await call_github_prs_api(client, owner=owner, repo=repo_name, token=access_token, cutoff=cutoff)
        
        runs = data.get("workflow_runs", [])
        
        # 1. Filter and build a definitive queue of valid targets
        items_to_process = []
        
        for run in runs:
            if run.get("conclusion") is None:
                continue
            items_to_process.append((run, 'workflow_run'))
                
        for pr in prs_data:
            # Note: Removing the 'merged_at' skip lets you log open/closed PRs.
            # If you ONLY want merged PRs, keep this filter active.
            if pr.get("merged_at"): 
                items_to_process.append((pr, 'pull_request'))
            
        # 2. Assign the true total count of items that will actually run
        start_job.total_items = len(items_to_process)
        db.commit()
        
        # 3. Guard against an empty database sync window
        if start_job.total_items == 0:
            start_job.progress = 100
        else:
            # 4. Process everything sequentially with a reliable counter
            for index, (payload, event_type) in enumerate(items_to_process):
                normalized_data = normalize_event(provider=provider, payload=payload, event=event_type)
                save_event(data=normalized_data, db=db, provider=provider)
                
                # Smooth sequential updates
                processed_count = index + 1
                start_job.processed_items = processed_count
                start_job.progress = int((processed_count / start_job.total_items) * 100)
                db.commit()
                
        start_job.status = "completed"
        start_job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        if 'start_job' in locals() and start_job:
            start_job.status = "failed"
            start_job.error_message = str(e)
            db.commit()
        
    finally:
        db.close()

    