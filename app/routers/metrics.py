
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Body,BackgroundTasks
from typing import Optional

from app.schemas.metrics import ChangeFailureRateResponse, DeploymentFrequencyResponse, LeadTimeResponse, MeanTimeToRecoveryResponse 
from app.services.metrics_services import   calculate_deployment_frequency, calculate_lead_time, calculate_change_failure_rate,calculate_mttr
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.events import Project
from app.services.sync_job_service import create_sync_job, fetch_historical_data,get_job_status
from app.services.metrics_services import (
    resolve_date_range, calculate_deployment_frequency, calculate_lead_time,
    calculate_change_failure_rate, calculate_mttr,
    calculate_daily_deployments, calculate_daily_lead_time,
    calculate_daily_change_failure_rate, calculate_daily_mttr,
    calculate_engineering_overview
)
from pydantic import BaseModel

class ProjectRegisterRequest(BaseModel):
    external_id: str
    name: str
    web_url: str
    provider: str

class BackFillRequest(BaseModel):
    project_id:int
    repo_name:str
    owner:str
    provider:str
    access_token:str
    gitlab_project_id:str


    
router = APIRouter()

#helper function to check if project exists
def check_project_exists(project_id: int, db: Session):
    project = db.execute(select(Project).filter_by(id=project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/projects")
def get_projects(db:Session = Depends(get_db)):
    projects = db.execute(select(Project)).scalars().all()
    return [{"id":p.id,"external_id":p.external_id ,"name":p.name,"web_url":p.web_url, "provider": p.provider}for p in projects]
@router.get("/deployment-frequency", response_model=DeploymentFrequencyResponse)
def calculate_metrics(project_id: int, days: int = 90,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None ,db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
    
    # Placeholder for actual metrics calculation logic
    # In a real implementation, you would calculate the metrics based on the input data
    start_date,end_date = resolve_date_range(days,start_date,end_date)
    metrics = calculate_deployment_frequency(project_id, start_date,end_date, db)

    return DeploymentFrequencyResponse(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        calculated_at=datetime.utcnow(),
        total_deployments=metrics["total_deployments"],
        daily_average=metrics["daily_average"],
        frequency_label=metrics["frequency_label"]
    )
@router.post("/projects")
def register_project(payload: ProjectRegisterRequest, db: Session = Depends(get_db)):
    project = db.execute(select(Project).where(
        Project.external_id == payload.external_id,
        Project.provider == payload.provider
    )).scalar_one_or_none()

    if not project:
        project = Project(
            external_id=payload.external_id,
            name=payload.name,
            web_url=payload.web_url,
            provider=payload.provider
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    return {"id": project.id, "name": project.name} 

@router.get("/lead-time", response_model=LeadTimeResponse)
def get_lead_time(project_id: int,days: int = 90,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None,db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
    
    # Calculate the cutoff date
    start_date,end_date = resolve_date_range(days,start_date,end_date)
    metrics = calculate_lead_time(project_id, start_date,end_date,db)

    return LeadTimeResponse(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        calculated_at=datetime.utcnow(),
        average_lead_time_hours=metrics["average_lead_time_hours"]
    )

@router.get("/change-failure-rate", response_model=ChangeFailureRateResponse)
def get_change_failure_rate(project_id: int, days: int = 90,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None, db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
   
    # Calculate the cutoff date
    start_date,end_date = resolve_date_range(days,start_date,end_date)
    metrics = calculate_change_failure_rate(project_id, start_date,end_date,db)

    return ChangeFailureRateResponse(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        calculated_at=datetime.utcnow(),
        failure_rate_percentage=metrics["failure_rate_percentage"]
    )

@router.get("/mean-time-to-recovery", response_model=MeanTimeToRecoveryResponse)
def get_mean_time_to_recovery(project_id: int, days: int = 90,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None, db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
    
    # Calculate the cutoff date
    start_date,end_date = resolve_date_range(days,start_date,end_date)
    metrics = calculate_mttr(project_id, start_date,end_date,db)
    


    return MeanTimeToRecoveryResponse(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        calculated_at=datetime.utcnow(),
        avg_mttr=metrics["avg_mttr"]
    )

@router.get("/trends")
def get_trends(project_id:int, days:int = 90,start_date:Optional[datetime]=None,end_date:Optional[datetime]=None, db:Session =Depends(get_db)):
    check_project_exists(project_id, db)
    start_date,end_date = resolve_date_range(days,start_date,end_date)
    return {
        "deployment_frequency": calculate_daily_deployments(project_id, start_date,end_date, db),
        "lead_time": calculate_daily_lead_time(project_id, start_date, end_date,db),
        "change_failure_rate": calculate_daily_change_failure_rate(project_id,start_date,end_date,db),
        "mttr": calculate_daily_mttr(project_id, start_date,end_date,db),
    }

@router.post("/events/backfill")
async def registerBackfill(payload:BackFillRequest,background_tasks:BackgroundTasks ,db:Session=Depends(get_db)):
    job = create_sync_job(payload.project_id,payload.provider,"pending", db)
    background_tasks.add_task(fetch_historical_data,job.id,payload.project_id,payload.owner,payload.repo_name,payload.provider, payload.access_token,payload.gitlab_project_id)
    return {"sync_job_id":job.id} 

@router.get("/sync-status/{sync_job_id}")
async def check_sync_status(sync_job_id: int, db: Session = Depends(get_db)):
    status = get_job_status(sync_job_id, db)

    if not  status:
        raise HTTPException(status_code=404, detail="Sync job not found")


    return {
    "sync_job_id": status.id,
    "status": status.status,
    "progress": status.progress,
    "processed_items": status.processed_items,
    "total_items": status.total_items,
    "error_message": status.error_message
}

@router.get("/engineering-overview")
def get_engineering_metrics(project_id:int, days:int=90, start_date:Optional[datetime]=None,end_date:Optional[datetime]=None, db:Session=Depends(get_db)):
    check_project=check_project_exists(project_id,db)

    
    start_date,end_date= resolve_date_range(days,start_date,end_date)
    result = calculate_engineering_overview(project_id,start_date,end_date,db)
   
    

    return result
