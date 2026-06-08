from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select,and_, func
from app.models.events import Event, Project


def calculate_frequency_label(daily_average) -> str:
    if daily_average >= 1:
        return "Multiple Deployments per Day"
    elif daily_average == 0:
        return "No deployments"
    
    elif daily_average >= 0.14:
        return "Multiple Deployments per Week"
    elif daily_average >= 0.07:
        return "Once per Week"
    elif daily_average < 0.07:
        return "Once per month"
    
def base_pipeline_query(project_id:int, cutoff: datetime):
    
    return select(Event).where(and_(
        Event.project_id == project_id,
        Event.event_type == "pipeline",
        Event.timestamp >= cutoff
    ))    

def calculate_cutoff(days:int):
    return datetime.now(timezone.utc) - timedelta(days=days)

def calculate_daily_deployments(project_id:int,cutoff:datetime,db:Session):
    date_label= func.date(Event.timestamp).label("deployment_day")
    query = (
        select(date_label, func.count(Event.id).label("daily_count"))
        .where(and_(
            Event.project_id == project_id,
            Event.event_type == "pipeline",
            Event.status == "success",
            Event.timestamp >= cutoff

        ))
        .group_by(date_label)
        .order_by(date_label)
    )
    results = db.execute(query).all()
    return [{"date":str(row.deployment_day), "value":row.daily_count} for row in results]

def calculate_daily_lead_time(project_id: int, cutoff: datetime, db: Session):
    date_label = func.date(Event.timestamp).label("lead_time_day")

    query = (
        select(
            date_label,
            func.avg(
                func.extract('epoch', Event.finished_at - Event.created_at) / 3600
            ).label("avg_lead_time")
        )
        .where(and_(
            Event.project_id == project_id,
            Event.event_type == "merge_request",
            Event.status == "success",
            Event.timestamp >= cutoff
        ))
        .group_by(date_label)
        .order_by(date_label)
    )
    results = db.execute(query).all()
    return [{"date": str(row.lead_time_day), "value": row.avg_lead_time} for row in results]


def calculate_daily_change_failure_rate(project_id:int, cutoff:datetime, db:Session):
    date_label = func.date(Event.timestamp).label("daily_cfr")
    
    failed_count = func.count().filter(Event.status == "failed").label("failed_deployments")
    query = select(
        date_label, (failed_count * 100 / func.count()).label("cfr")
    ).where(and_(
        Event.project_id == project_id,
        Event.event_type == "pipeline",
        Event.timestamp >= cutoff
    )).group_by(date_label).order_by(date_label)
    results = db.execute(query).all()
    return [{"date": str(row.daily_cfr), "value": row.cfr} for row in results]

def calculate_daily_mttr(project_id: int, cutoff: datetime, db: Session):
    
    failed_event_result = select(Event).where(and_(Event.project_id == project_id,
                                                   Event.event_type == "pipeline",
                                                   Event.status == "failed",
                                                   Event.timestamp >=  cutoff)).order_by(Event.timestamp)
    failed_event = db.execute(failed_event_result).scalars().all()
    recovery_times = {}
    for event in failed_event:
        recovery= db.execute(select(Event).where(and_(
            Event.project_id ==project_id,
            Event.event_type == "pipeline",
            Event.status == "success",
            Event.created_at > event.finished_at
        )).order_by(Event.created_at).limit(1)).scalar_one_or_none()
        day = event.timestamp.date()
        if recovery:
            diff = (recovery.created_at - event.finished_at).total_seconds()/3600
            if day not in recovery_times:
                recovery_times[day]=[]
            recovery_times[day].append(diff)
    return[{"date":str(day), "value":sum(times)/len(times)}
           for day,
            times in recovery_times.items()
           ]            
            
            



def calculate_deployment_frequency(project_id:int, cutoff: datetime, db: Session):
    
    query = base_pipeline_query(project_id, cutoff)
    result = select(func.count()).select_from(query.subquery())
    total_deployments = db.execute(result).scalar()

    # Calculate the number of days in the period
    days = (datetime.now(timezone.utc) - cutoff).days or 1
    daily_average = total_deployments / days
    frequency_label = calculate_frequency_label(daily_average)
    

    return {
        "total_deployments": total_deployments,
        "daily_average": daily_average,
        "frequency_label": frequency_label
    }

def calculate_lead_time(project_id:int, db:Session, cutoff: datetime):
    #average time between created at and finished at for successful merge request events
    
    result = select(func.avg(func.extract('epoch',Event.finished_at - Event.created_at)/3600)).where(and_(Event.project_id == project_id, Event.event_type == "merge_request", Event.status == "success", Event.timestamp >= cutoff))
    average_lead_time_hours = db.execute(result).scalar() or 0.0

    return {
        "average_lead_time_hours": average_lead_time_hours
    }

def calculate_change_failure_rate(project_id:int, db:Session, cutoff: datetime):
    query = base_pipeline_query(project_id, cutoff)
    total_deployments_result = select(func.count()).select_from(query.subquery())
    total_deployments = db.execute(total_deployments_result).scalar()
    failed_deployments_result = select(func.count(Event.id)).where(and_(Event.project_id == project_id, Event.event_type == "pipeline", Event.status == "failure", Event.timestamp >= cutoff))
    failed_deployments = db.execute(failed_deployments_result).scalar()
    failure_rate_percentage = (failed_deployments / total_deployments) * 100 if total_deployments > 0 else 0

    return {
        "failure_rate_percentage": failure_rate_percentage
    }


def calculate_mttr(project_id: int, db: Session, cutoff: datetime):
    # find all failed events
    failed_event_result = select(Event).where(and_(Event.project_id == project_id, Event.event_type == "pipeline", Event.status == "failure", Event.timestamp >= cutoff)).order_by(Event.timestamp)
    failed_event = db.execute(failed_event_result).scalars().all()
    # for each failure, find the next success after it
    recovery_times = []
    for event in failed_event:
        recovery = db.execute(select(Event).where(and_(
            Event.project_id == project_id,
            Event.event_type == "pipeline",
            Event.status == "success",
            Event.created_at > event.created_at
        )).order_by(Event.created_at).limit(1)).scalar_one_or_none() 
        if recovery:
            print("event", event.created_at, event.finished_at)           
            print("recovery", recovery.created_at, recovery.finished_at)
            diff = (recovery.created_at - event.finished_at).total_seconds() / 3600  # Convert to hours
            recovery_times.append(diff)
    # calculate average time difference
    avg_mttr = sum(recovery_times) / len(recovery_times) if recovery_times else 0

    return {
        "avg_mttr": avg_mttr
    }