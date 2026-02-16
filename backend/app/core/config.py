# [IMMUTABLE CORE] 이 파일은 프로젝트의 핵심 아키텍처(Supabase/API)를 정의합니다.
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
    
    # Sync Optimization
    SYNC_RAW_DAYS: int = 3       # 최근 며칠간의 원본 데이터를 매번 가져와 정합성 유지
    SYNC_BACKFILL_DAYS: int = 7  # 누락된 RECONCILED 데이터를 채워넣는 소급 기간
    
    # Naver Open API (Login / Trend)
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    NAVER_REDIRECT_URI: str = "http://localhost:8000/api/v1/naver/callback"
    
    # Auth
    SECRET_KEY: str = "dmind-secret-key-123456789"
    ADMIN_EMAIL: str = "admin@dmind.com"
    ADMIN_PASSWORD: str = "admin123!"

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        """
        [EXPLICIT] Returns the database URL strictly from environment variables.
        No auto-correction or hidden logic.
        """
        if not self.DATABASE_URL:
            return "sqlite:///./test.db"
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
