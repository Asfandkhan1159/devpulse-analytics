from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


from app.db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_table.id"))
    provider = Column(String,index=True)
    event_type = Column(String, index=True)
    timestamp = Column(DateTime)
    status = Column(String, index=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime)
    actor=Column(String,nullable=True)
    branch=Column(String, nullable=True)
    commit_count = Column(String, nullable=True)
    external_event_id = Column(String, nullable=True, index=True)
    actor_email = Column(String, nullable=True)
    actor_username = Column(String, nullable=True)



class Project(Base):
    __tablename__ = "project_table"
    id= Column(Integer, primary_key=True, index=True)
    external_id= Column(String, index=True)
    provider = Column(String, index=True)
    name= Column(String, index=True)
    web_url= Column(String, index=True)    

class SyncJob(Base):
    __tablename__="sync_jobs"
    id = Column(Integer,primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_table.id"))
    provider=Column(String,index=True)
    status=Column(String,index=True)
    processed_items=Column(Integer,nullable=True)
    total_items=Column(Integer,nullable=True)  
    progress = Column(Integer,index=True,nullable=True)
    error_message=Column(String,nullable=True)
    created_at=Column(DateTime)
    completed_at=Column(DateTime,nullable=True)
