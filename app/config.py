from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gitlab_token:str
    database_url:str

    class Config:
        env_file = ".env"
    
