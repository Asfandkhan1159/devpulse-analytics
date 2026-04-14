from app.services.webhook_service import save_event
from app.db.database import SessionLocal
from sqlalchemy import select, and_,func
from app.models.events import Event, Project
from app.services.metrics_services import base_pipeline_query

def test_save_event(db_session):
    # Create a test database session
   

    # arrange
    payload = {
        "project_id": 123,
        "project": {
            "id": 123,
            "name": "Test Project",
            "web_url": "http://gitlab.com/test_project"
        },
        "object_kind": "pipeline",
        "object_attributes": {
            "status": "success",
            "finished_at": "2024-06-01T12:00:00Z",
            "created_at": "2024-06-01T10:00:00Z"
        }
    }

    # Call the save_event function
    event = save_event(payload, db_session)
    db_session.commit()  # Commit the transaction to save the event in the database

    assert event.event_type == "pipeline"
    assert event.status == "success"
    assert event.project_id is not None 

def test_save_event_creates_project_if_not_exists(db_session):
    #arrange
    payload = {
        "project_id": 456,
        "project": {
            "id": 456,
            "name": "New Project",
            "web_url": "http://gitlab.com/new_project"
        },
        "object_kind": "pipeline",
        "object_attributes": {
            "status": "failed",
            "finished_at": "2024-06-01T14:00:00Z",
            "created_at": "2024-06-01T13:00:00Z"
        }
    }
    #act if project does not exist, it should be created
    save_event(payload, db_session)
    save_event(payload, db_session)
    
    db_session.commit()  # Commit the transaction to save the event and project in the database
    
    #query the project
    project = db_session.execute(select(func.count(Project.id)).filter_by(gitlab_project_id=456)).scalar_one_or_none()
    #assert
    assert project == 1  # There should be exactly one project with gitlab_project_id 456
    

    
