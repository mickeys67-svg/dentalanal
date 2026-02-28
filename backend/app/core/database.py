# [IMMUTABLE CORE] DB 엔진 및 세션 관리.
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

SQLALCHEMY_DATABASE_URL = settings.get_database_url

# Handle Render/Supabase/Heroku postgres:// vs postgresql:// issue
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

import logging
logger = logging.getLogger(__name__)

# Log the database type (but mask password)
masked_url = SQLALCHEMY_DATABASE_URL
if "@" in SQLALCHEMY_DATABASE_URL:
    prefix = SQLALCHEMY_DATABASE_URL.split("://")[0]
    host_part = SQLALCHEMY_DATABASE_URL.split("@")[-1]
    masked_url = f"{prefix}://****@{host_part}"

# logger.info(f"Database connection initialized: {masked_url}")
logger.info(f"Database connection initialized: {masked_url}")

# Database Engine Configuration
connect_args = {}
engine_args = {
    "pool_pre_ping": True,
}

# PostgreSQL / Supabase PgBouncer (port 6543) 최적화
# Supabase free tier PgBouncer 최대 60 연결. Cloud Run 서버리스 환경에서
# 인스턴스가 여러 개 뜰 수 있으므로 인스턴스당 연결을 최소화.
engine_args.update({
    "pool_size": 3,       # 인스턴스당 기본 연결 수
    "max_overflow": 7,    # 최대 burst 연결 (총 10)
    "pool_recycle": 300,  # 5분마다 연결 재생성 (Supabase idle timeout 대응)
    "pool_timeout": 10,   # 연결 대기 최대 10초
})

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    **engine_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
