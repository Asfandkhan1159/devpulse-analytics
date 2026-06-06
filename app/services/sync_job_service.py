from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime
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

async def fetch_historical_data(sync_job_id: int,
    project_id: int,
    owner: str,
    repo_name: str,
    provider: str,
    access_token: str,
   ):
    try:
        db = SessionLocal()
        start_job= get_job_status(sync_job_id,db)

        start_job.status = "in_progress"
        
        cutoff = calculate_cutoff(90)
        async with httpx.AsyncClient() as client :
            data = await call_github_api(client, owner=owner, repo = repo_name, token = access_token, cutoff=cutoff)
        runs = data ["workflow_runs"]
        start_job.total_items = len(runs)
        db.commit()
        for i, run in enumerate(runs):
            if not run.get("conclusion"):
                continue
            normalized_github_data=normalize_event(provider=provider, payload=run, event='workflow_run')
            save_event(data=normalized_github_data, db=db, provider=provider)
            start_job.processed_items= i + 1
            start_job.progress = int(((i + 1)/start_job.total_items)*100)
            db.commit()
        start_job.status = "completed"
        start_job.completed_at = datetime.utcnow()
        db.commit()        


    except Exception as e:
        start_job.status = "failed"
        start_job.error_message = str(e)
        db.commit()

        
    finally:
        db.close()
   
    