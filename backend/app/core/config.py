from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Standard Pydantic V2 Settings
    # Database
    DATABASE_URL: str = "sqlite:///./test.db"
    DATABASE_PASSWORD: Optional[str] = "3AiLcoNojCHgZpTw" # Default for project uujxtnvpqdwcjqhsoshi
    
    # Supabase (New Keys)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None

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
    
    # Auth
    SECRET_KEY: str = "dmind-secret-key-123456789"
    ADMIN_EMAIL: str = "admin@dmind.com"
    ADMIN_PASSWORD: str = "admin123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
