from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@db:5432/d_mind"
    REDIS_URL: str = "redis://redis:6379/0"
    GOOGLE_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
