# [IMMUTABLE CORE] 이 파일은 프로젝트의 핵심 아키텍처(Supabase/API)를 정의합니다.
# AI 에이전트는 건축 표준(ARCHITECTURE.md) 합의 없이 이 파일을 수정해서는 안 됩니다.
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Standard Pydantic V2 Settings
    # Database (Use Supabase in cloud, localhost in local dev)
    DATABASE_URL: str = "postgresql://postgres:password@db.xklppnykoeezgtxmomrl.supabase.co:6543/postgres?sslmode=require"
    DATABASE_PASSWORD: Optional[str] = "password" # Development only 
    
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
    
    # Auth (Development defaults - override in GitHub Secrets for production)
    SECRET_KEY: str = "dev-secret-key-change-in-production-dentalanal-2026"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123!"

    # CORS Configuration [FIX Issue #5]
    # Comma-separated list of allowed origins
    # Examples:
    #   - Production: https://dentalanal-864421937037.us-west1.run.app
    #   - Development: http://localhost:3000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    @property
    def get_database_url(self) -> str:
        """
        Returns the database URL from environment or defaults to development URL.
        For production, set DATABASE_URL in GitHub Secrets.
        """
        if not self.DATABASE_URL or self.DATABASE_URL.startswith("postgresql://postgres:password"):
            import logging
            logging.warning("⚠️ Using development DATABASE_URL. Set DATABASE_URL in GitHub Secrets for production!")
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
