from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from datetime import datetime, timezone
from app.db.database import SessionLocal
import httpx
from app.models.events import SyncJob

from app.services.metrics_services import resolve_date_range
from app.services.normalizers.factory import normalize_event
from app.services.webhook_service import save_event
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
base_Url_github ="https://api.github.com" 
base_Url_gitlab="https://gitlab.com/api/v4"



def with_retry(func):
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException))
    )(func)


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

@with_retry
async def call_github_api(client:httpx.AsyncClient, owner:str, repo:str, token:str,start_date:datetime) -> dict:
    
    headers={
        "Authorization":f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
    }

    response = await client.get(f"{base_Url_github}/repos/{owner}/{repo}/actions/runs", headers=headers, 
                                params={
                                    "per_page":100,
                                    "created":f"{start_date.strftime('%Y-%m-%d')}..{datetime.utcnow().strftime('%Y-%m-%d')}"
                                })

    response.raise_for_status()
    return response.json()

@with_retry
async def call_gitlab_pipelines_api(client: httpx.AsyncClient, gitlab_project_id: str, token: str, start_date: datetime) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get(
        f"{base_Url_gitlab}/projects/{gitlab_project_id}/pipelines",
        headers=headers,
        params={
            "per_page": 100,
            "updated_after": start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        }
    )
    response.raise_for_status()
    return response.json()

@with_retry
async def call_github_prs_api(client:httpx.AsyncClient, owner:str, repo:str, token:str, start_date:datetime) ->dict:
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
            pr_updated_at = datetime.strptime(pr["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            if pr_updated_at >= start_date:
                pull_requests.append(pr)
            else:
                return pull_requests
        if len(data) < 100:
            break
        page +=1
    return pull_requests          

@with_retry
async def call_gitlab_mrs_api(client:httpx.AsyncClient,gitlab_project_id,token,start_date):  
    headers = {"Authorization": f"Bearer {token}"}
    merge_requests = []
    page = 1
    while True:
        response = await client.get(
        f"{base_Url_gitlab}/projects/{gitlab_project_id}/merge_requests",
        headers=headers,
        params={
            "state":"merged",
            "per_page": 100,
            "updated_after": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "page":page
        }
    )
        response.raise_for_status()
        data = response.json()

        if not data:
            break
        for mr in data:
            mr_updated_at = datetime.strptime(mr["updated_at"],"%Y-%m-%dT%H:%M:%SZ")
            if mr_updated_at >= start_date:
                merge_requests.append(mr)
            else:
                return merge_requests
        if len(data) < 100:
            break
        page +=1
    return merge_requests            



async def fetch_historical_data(
    sync_job_id: int,
    project_id: int,
    owner: str,           # For GitHub: org/user, For GitLab: group or ignore if using project_id
    repo_name: str,       # For GitHub: repo name, For GitLab: project path or ID as string
    provider: str,        # "github" or "gitlab"
    access_token: str,
    gitlab_project_id: str = None,  # Required for GitLab
):

    try:
        db = SessionLocal()
        start_job = get_job_status(sync_job_id, db)
        if not start_job:
            raise ValueError("SyncJob not found")

        start_job.status = "in_progress"
        db.commit()

        start_date,end_date = resolve_date_range(90)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if provider.lower() == "github":
                runs_data = await call_github_api(client, owner, repo_name, access_token, start_date)
                prs_data = await call_github_prs_api(client, owner, repo_name, access_token, start_date)
                
                runs = runs_data.get("workflow_runs", [])
                items_to_process = []

                for run in runs:
                    if run.get("conclusion") is None:
                        continue
                    items_to_process.append((run, 'workflow_run'))

                for pr in prs_data:
                    if pr.get("merged_at"):   # Only merged PRs? Or remove this if you want all
                        items_to_process.append((pr, 'pull_request'))

            elif provider.lower() == "gitlab":
                if not gitlab_project_id:
                    raise ValueError("gitlab_project_id is required for GitLab provider")

                pipelines = await call_gitlab_pipelines_api(client, gitlab_project_id, access_token, start_date)
                mrs = await call_gitlab_mrs_api(client, gitlab_project_id, access_token, start_date)

                items_to_process = []

                for pipeline in pipelines:
                    if pipeline.get("status") in ["success", "failed"]:  # Only completed ones
                        items_to_process.append((pipeline, 'pipeline'))

                for mr in mrs:
                    if mr.get("merged_at"):   # Adjust filter as needed
                        items_to_process.append((mr, 'merge_request'))

            else:
                raise ValueError(f"Unsupported provider: {provider}")

        # Common processing logic
        start_job.total_items = len(items_to_process)
        db.commit()

        if start_job.total_items == 0:
            start_job.progress = 100
            start_job.status = "completed"
            start_job.completed_at = datetime.utcnow()
            db.commit()
            return

        for index, (payload, event_type) in enumerate(items_to_process):
            normalized_data = normalize_event(
                provider=provider, 
                payload=payload, 
                event=event_type
            )
            save_event(data=normalized_data, db=db, provider=provider)

            processed_count = index + 1
            start_job.processed_items = processed_count
            start_job.progress = int((processed_count / start_job.total_items) * 100)
            if processed_count % 10 == 0:
                db.commit()

        start_job.status = "completed"
        start_job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        if 'start_job' in locals() and start_job:
            import traceback
            start_job.status = "failed"
            start_job.error_message = traceback.format_exc()[:2500]
            db.commit()
       

    finally:
        db.close()