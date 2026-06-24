from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, text,cast,Interval
from app.models.events import Event


def calculate_frequency_label(daily_average: float) -> str:
    if daily_average >= 1.0:
        return "Multiple Deployments per Day"
    elif daily_average >= 0.14:
        return "Multiple Deployments per Week"
    elif daily_average >= 0.07:
        return "Once per Week"
    else:
        return "Once per month or less"


def resolve_date_range(
    days: int = 90, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
):
    end = end_date or datetime.now()
    start = start_date or (end - timedelta(days=days))
    
    if start > end:
        start, end = end, start

    return start, end


def base_pipeline_query(project_id: int, start_date: datetime, end_date: datetime):
    return select(Event).where(
        and_(
            Event.project_id == project_id,
            Event.event_type == "pipeline",
            Event.timestamp >= start_date,
            Event.timestamp <= end_date
        )
    )


def calculate_daily_deployments(project_id: int, start_date: datetime, end_date: datetime, db: Session):
    date_label = func.date(Event.timestamp).label("deployment_day")
    query = (
        select(date_label, func.count(Event.id).label("daily_count"))
        .where(and_(
            Event.project_id == project_id,
            Event.event_type == "pipeline",
            Event.status == "success",
            Event.timestamp >= start_date,
            Event.timestamp <= end_date
        ))
        .group_by(date_label)
        .order_by(date_label)
    )
    results = db.execute(query).all()
    return [{"date": str(row.deployment_day), "value": row.daily_count} for row in results]


def calculate_daily_lead_time(project_id: int, start_date: datetime, end_date: datetime, db: Session):
    date_label = func.date(Event.timestamp).label("lead_time_day")
    query = (
        select(
            date_label,
            func.avg(func.extract('epoch', Event.finished_at - Event.created_at) / 3600).label("avg_lead_time")
        )
        .where(and_(
            Event.project_id == project_id,
            Event.event_type == "merge_request",
            Event.status == "success",
            Event.timestamp >= start_date,
            Event.timestamp <= end_date
        ))
        .group_by(date_label)
        .order_by(date_label)
    )
    results = db.execute(query).all()
    return [{"date": str(row.lead_time_day), "value": row.avg_lead_time} for row in results]


def calculate_daily_change_failure_rate(project_id: int, start_date: datetime, end_date: datetime, db: Session):
    date_label = func.date(Event.timestamp).label("daily_cfr")
    failed_count = func.count().filter(Event.status == "failure").label("failed_deployments")
    
    query = select(
        date_label, (failed_count * 100 / func.count()).label("cfr")
    ).where(and_(
        Event.project_id == project_id,
        Event.event_type == "pipeline",
        Event.timestamp >= start_date,
        Event.timestamp <= end_date
    )).group_by(date_label).order_by(date_label)
    
    results = db.execute(query).all()
    return [{"date": str(row.daily_cfr), "value": row.cfr} for row in results]


def calculate_daily_mttr(project_id: int, start_date: datetime, end_date: datetime, db: Session):
   s = Event.__table__.alias("s")

   next_success =(
       select(func.min(s.c.created_at))
       .where(and_(
           s.c.project_id == Event.project_id,
           s.c.event_type == "pipeline",
           s.c.status == "success",
           s.c.created_at >func.coalesce(Event.finished_at,Event.created_at)
           

       ))
       .correlate(Event)
       .scalar_subquery()
   )

   query = (
       select(
           func.date(Event.timestamp).label("day"),
           func.avg(func.extract("epoch",next_success - func.coalesce(Event.finished_at,Event.created_at))/3600).label("avg_mttr")
       )
   ).where(and_(
       Event.project_id == project_id,
       Event.event_type == "pipeline",
       Event.status == "failure",
       Event.timestamp >= start_date,
       Event.timestamp <= end_date

   )).group_by(func.date(Event.timestamp)).order_by(func.date(Event.timestamp))
    
   results = db.execute(query).all()
   return [{"date": str(row.day), "value": row.avg_mttr} for row in results]

   

   


def calculate_deployment_frequency(project_id: int, start_date: datetime, end_date: datetime, db: Session):
    query = base_pipeline_query(project_id, start_date, end_date)
    total_deployments = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar() or 0

    days_period = (end_date - start_date).days or 1
    daily_average = total_deployments / days_period
    frequency_label = calculate_frequency_label(daily_average)

    return {
        "total_deployments": total_deployments,
        "daily_average": daily_average,
        "frequency_label": frequency_label
    }


def calculate_lead_time(project_id: int,  start_date: datetime, end_date: datetime,db: Session,):
    result = db.execute(
        select(func.avg(func.extract('epoch', Event.finished_at - Event.created_at) / 3600))
        .where(and_(
            Event.project_id == project_id,
            Event.event_type == "merge_request",
            Event.status == "success",
            Event.timestamp >= start_date,
            Event.timestamp <= end_date
        ))
    ).scalar() or 0.0

    return {"average_lead_time_hours": result}


def calculate_change_failure_rate(project_id: int,  start_date: datetime, end_date: datetime,db: Session,):
    query = base_pipeline_query(project_id, start_date, end_date)
    total_deployments = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar() or 0

    failed = db.execute(
        select(func.count(Event.id)).where(and_(
            Event.project_id == project_id,
            Event.event_type == "pipeline",
            Event.status == "failure",
            Event.timestamp >= start_date,
            Event.timestamp <= end_date
        ))
    ).scalar() or 0

    failure_rate = (failed / total_deployments * 100) if total_deployments > 0 else 0
    return {"failure_rate_percentage": failure_rate}


def calculate_mttr(project_id: int,  start_date: datetime, end_date: datetime,db: Session):
    # Alias for the success events subquery
    s = Event.__table__.alias("s")
    
    # Inner correlated subquery — finds earliest success after each failure
    next_success = (
        select(func.min(s.c.created_at))
        .where(and_(
            s.c.project_id == Event.project_id,
            s.c.event_type == "pipeline",
            s.c.status == "success",
            s.c.created_at > func.coalesce(Event.finished_at, Event.created_at)
        ))
        .correlate(Event)
        .scalar_subquery()
    )
    
    # Outer query — groups by day, averages recovery time
    query = (
        select(
            
            func.avg(
                func.extract("epoch", next_success - func.coalesce(Event.finished_at, Event.created_at)) / 3600
            ).label("avg_mttr")
        )
        .where(and_(
            Event.project_id == project_id,
            Event.event_type == "pipeline",
            Event.status == "failure",
            Event.timestamp >= start_date,
            Event.timestamp <= end_date
        ))
        
    )
    
    result = db.execute(query).scalar() or 0
    return {"avg_mttr": result}