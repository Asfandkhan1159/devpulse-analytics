
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException


from app.schemas.metrics import ChangeFailureRateResponse, DeploymentFrequencyResponse, LeadTimeResponse, MeanTimeToRecoveryResponse 
from app.services.metrics_services import  calculate_cutoff, calculate_deployment_frequency, calculate_lead_time, calculate_change_failure_rate,calculate_mttr
from app.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.events import Project

router = APIRouter()

#helper function to check if project exists
def check_project_exists(project_id: int, db: Session):
    project = db.execute(select(Project).filter_by(id=project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project



@router.get("/deployment-frequency", response_model=DeploymentFrequencyResponse)
def calculate_metrics(project_id: int, days: int = 30, db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
    
    # Placeholder for actual metrics calculation logic
    # In a real implementation, you would calculate the metrics based on the input data
    cutoff_date = calculate_cutoff(days)
    metrics = calculate_deployment_frequency(project_id, cutoff_date, db)

    return DeploymentFrequencyResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        total_deployments=metrics["total_deployments"],
        daily_average=metrics["daily_average"],
        frequency_label=metrics["frequency_label"]
    )

@router.get("/lead-time", response_model=LeadTimeResponse)
def get_lead_time(project_id: int,days: int = 30 ,db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
    
    # Calculate the cutoff date
    cutoff_date = calculate_cutoff(days)
    metrics = calculate_lead_time(project_id, db, cutoff_date)

    return LeadTimeResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        average_lead_time_hours=metrics["average_lead_time_hours"]
    )

@router.get("/change-failure-rate", response_model=ChangeFailureRateResponse)
def get_change_failure_rate(project_id: int, days: int = 30, db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
   
    # Calculate the cutoff date
    cutoff_date = calculate_cutoff(days)
    metrics = calculate_change_failure_rate(project_id, db, cutoff_date)

    return ChangeFailureRateResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        failure_rate_percentage=metrics["failure_rate_percentage"]
    )

@router.get("/mean-time-to-recovery", response_model=MeanTimeToRecoveryResponse)
def get_mean_time_to_recovery(project_id: int, days: int = 30, db: Session = Depends(get_db)):
    check_project = check_project_exists(project_id, db)
    
    # Calculate the cutoff date
    cutoff_date = calculate_cutoff(days)
    metrics = calculate_mttr(project_id, db, cutoff_date)
    print("printing mttr", metrics["avg_mttr"])


    return MeanTimeToRecoveryResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        avg_mttr=metrics["avg_mttr"]
    )

