import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.models.events import Event, Project


TEST_DATABASE_URL = "postgresql://devpulse:devpulse123@localhost:5433/devpulse_test"

engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    
@pytest.fixture(scope="session")
def db_session():
    # Create the database tables from Event and Project models
    Base.metadata.create_all(bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop the tables after the test
        Base.metadata.drop_all(bind=engine)
