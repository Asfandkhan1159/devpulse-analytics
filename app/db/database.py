# database.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# FIX 2: Import the instantiated "settings" object, NOT the class
from app.config import settings 

class Base(DeclarativeBase):
    pass

# Remove the duplicate "settings = Settings()" lines here

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
