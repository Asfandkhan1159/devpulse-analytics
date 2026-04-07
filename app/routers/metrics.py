
from datetime import datetime

from fastapi import APIRouter, Depends


from app.schemas.metrics import ChangeFailureRateResponse, DeploymentFrequencyResponse, LeadTimeResponse, MeanTimeToRecoveryResponse 
from app.services.metrics_services import calculate_deployment_frequency
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()



@router.get("/deployment-frequency", response_model=DeploymentFrequencyResponse)
def calculate_metrics(project_id: int, days: int = 30, db: Session = Depends(get_db)):
    # Placeholder for actual metrics calculation logic
    # In a real implementation, you would calculate the metrics based on the input data
    metrics = calculate_deployment_frequency( project_id, days,db)

    return DeploymentFrequencyResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        total_deployments=metrics["total_deployments"],
        daily_average=metrics["daily_average"]
    )

@router.get("/lead-time", response_model=LeadTimeResponse)
def calculate_lead_time(project_id: int, days: int = 30):

    return LeadTimeResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        average_lead_time_hours=5.5  # Example value
    )

@router.get("/change-failure-rate", response_model=ChangeFailureRateResponse)
def calculate_change_failure_rate(project_id: int, days: int = 30):

    return ChangeFailureRateResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        failure_rate_percentage=12.5  # Example value
    )

@router.get("/mean-time-to-recovery", response_model=MeanTimeToRecoveryResponse)
def calculate_mean_time_to_recovery(project_id: int, days: int = 30):

    return MeanTimeToRecoveryResponse(
        project_id=project_id,
        period_days=days,
        calculated_at=datetime.utcnow(),
        mean_time_to_recovery_hours=8.0  # Example value
    )

