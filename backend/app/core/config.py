from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Standard Pydantic V2 Settings
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    GOOGLE_API_KEY: Optional[str] = None
    
    # Scraper & Ads
    BRIGHT_DATA_CDP_URL: Optional[str] = None
    GOOGLE_ADS_DEVELOPER_TOKEN: Optional[str] = None
    META_ADS_ACCESS_TOKEN: Optional[str] = None
    META_AD_ACCOUNT_ID: Optional[str] = None
    
    # Naver Search Ads API
    NAVER_AD_CUSTOMER_ID: Optional[str] = None
    NAVER_AD_ACCESS_LICENSE: Optional[str] = None
    NAVER_AD_SECRET_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
