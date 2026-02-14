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
    
    # Naver Open API (Login / Trend)
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    NAVER_REDIRECT_URI: str = "http://localhost:8000/api/v1/naver/callback"
    
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

def hydrate_settings_from_db():
    """
    [SELF-HEALING] DB에서 설정을 읽어와 settings 객체를 업데이트합니다.
    환경변수가 유실되었을 때를 대비한 2중 안전장치입니다.
    """
    try:
        from sqlalchemy import create_engine, text
        # settings 객체가 이미 생성된 후이므로 get_database_url 사용 가능
        temp_engine = create_engine(settings.get_database_url)
        with temp_engine.connect() as conn:
            # system_configs 테이블 존재 여부 확인 후 데이터 로드
            result = conn.execute(text("SELECT key, value FROM system_configs"))
            for key, value in result:
                if hasattr(settings, key) and not getattr(settings, key):
                    setattr(settings, key, value)
                    # print(f"[SELF-HEAL] DB에서 {key} 설정을 복구했습니다.")
    except Exception as e:
        # DB가 아직 준비되지 않았거나 테이블이 없는 경우 조용히 넘어감
        pass

settings = Settings()
# 서버 시작 시 자가 치유 실행
hydrate_settings_from_db()
