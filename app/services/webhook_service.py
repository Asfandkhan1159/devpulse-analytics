from sqlalchemy import  select
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.events import Event, Project



def save_event(payload: dict, db: Session) -> Event:
    # 1. extract project data from payload
    project_id = payload.get("project", {}).get("id")
    project_name = payload.get("project", {}).get("name")
    event_type = payload.get("object_kind")
    timestamp = datetime.utcnow()
    status = payload.get("object_attributes", {}).get("status")
    finished_at = payload.get("object_attributes", {}).get("finished_at")
    created_at = payload.get("object_attributes", {}).get("created_at")
    # 2. get or create project in DB
    project = db.execute(select(Project).filter_by(gitlab_project_id=project_id)).scalar_one_or_none()
    if not project:
        project = Project(gitlab_project_id=project_id, name=project_name, web_url=payload.get("project", {}).get("web_url"))
        db.add(project)
        db.flush()  # To get the project.id for the foreign key

    # 3. extract event data from payload
    event = Event(
        project_id=project.id,
        event_type=event_type,
        timestamp=timestamp,
        status=status,
        finished_at=finished_at,
        created_at=created_at
    )
    # 4. create and save event
    db.add(event)
    db.flush()

    # 5. return saved event
    return event