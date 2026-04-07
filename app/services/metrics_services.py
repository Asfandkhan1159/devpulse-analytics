from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select,and_, func
from app.models.events import Event, Project


def calculate_deployment_frequency(project_id:int, days:int,db: Session):
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    result = select(func.count(Event.id)).where(and_(Event.project_id == project_id, Event.event_type == "pipeline", Event.timestamp >= cutoff))
    total_deployments = db.execute(result).scalar()

    daily_average = total_deployments / days

    return {
        "total_deployments": total_deployments,
        "daily_average": daily_average
    }