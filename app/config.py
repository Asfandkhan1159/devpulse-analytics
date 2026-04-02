from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gitlab_token:str

    class Config:
        env_file = ".env"