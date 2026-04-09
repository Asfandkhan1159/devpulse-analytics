from pydantic_settings import BaseSettings
from pydantic import ConfigDict
class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")
    gitlab_token: str
    database_url: str
