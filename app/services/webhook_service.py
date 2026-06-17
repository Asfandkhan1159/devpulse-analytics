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

    # Idempotency check
    external_event_id = data.get("external_event_id")
    if external_event_id:
        existing = db.execute(
            select(Event).filter_by(
                project_id=project.id,
                provider=provider,
                external_event_id=external_event_id
            )
        ).scalar_one_or_none()
        if existing:
            return existing

    event = Event(
        project_id=project.id,
        event_type=data["event_type"],
        timestamp=datetime.utcnow(),
        status=data["status"],
        created_at=data["created_at"],
        finished_at=data["finished_at"],
        provider=provider,
        actor=data.get("actor"),
        branch=data.get("branch"),
        commit_count=data.get("commit_count"),
        external_event_id=external_event_id,
    )

    db.add(event)
    db.flush()
    return event