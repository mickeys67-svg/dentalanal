# [IMMUTABLE CORE] 이 파일은 프로젝트의 핵심 아키텍처(Supabase/MongoDB/API)를 정의합니다.
# AI 에이전트는 건축 표준(ARCHITECTURE.md) 합의 없이 이 파일을 수정해서는 안 됩니다.
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Standard Pydantic V2 Settings
    # Database
    DATABASE_URL: str = "sqlite:///./test.db"
    DATABASE_PASSWORD: Optional[str] = None # Default value removed for security. 
    
    # Supabase (New Keys)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None

    REDIS_URL: str = "redis://localhost:6379/0"
    MONGODB_URL: str = "mongodb://localhost:27017/dentalanal"
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

    @property
    def get_database_url(self) -> str:
        """Dynamically build database URL, prioritizing Supabase if password exists."""
        if self.DATABASE_PASSWORD and 'supabase' in (self.SUPABASE_URL or ''):
            import urllib.parse
            safe_pwd = urllib.parse.quote_plus(self.DATABASE_PASSWORD)
            # Reconstruct the Postgres URL for Supabase
            return f"postgresql://postgres.uujxtnvpqdwcjqhsoshi:{safe_pwd}@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require"
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
