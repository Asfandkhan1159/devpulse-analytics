from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_case_sensitive=False,
    )
    GITLAB_TOKEN: str
    DATABASE_URL: str
    DB_USERNAME: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_NAME: Optional[str] = None
    GATEWAY_DB_NAME: Optional[str] = None
    JWT_SECRET: Optional[str] = None

settings = Settings()