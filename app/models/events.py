from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship


from app.db.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_table.id"))
    event_type = Column(String, index=True)
    timestamp = Column(DateTime)
    status = Column(String, index=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime)




class Project(Base):
    __tablename__ = "project_table"
    id= Column(Integer, primary_key=True, index=True)
    gitlab_project_id= Column(Integer, index=True)
    name= Column(String, index=True)
    web_url= Column(String, index=True)        