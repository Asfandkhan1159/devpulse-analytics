from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.events import Event, Project


def save_event(data: dict, db: Session, provider: str) -> Event:

    project = db.execute(
        select(Project).filter_by(
            external_id=data["external_id"],
            provider=provider
        )
    ).scalar_one_or_none()

    if not project:
        project = Project(
            external_id=data["external_id"],
            name=data["project_name"],
            web_url=data["web_url"],
            provider=provider
        )

        db.add(project)
        db.flush()

    event = Event(
        project_id=project.id,
        event_type=data["event_type"],
        timestamp=datetime.utcnow(),
        status=data["status"],
        created_at=data["created_at"],
        finished_at=data["finished_at"],
        provider=provider
    )

    db.add(event)
    db.flush()

    return event