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
# PgBouncer(port 6543) 호환 설정 - prepared statement 충돌 방지
connect_args = {
    "options": "-c statement_timeout=30000"  # 개별 쿼리 30초 제한
}
engine_args = {
    "pool_pre_ping": True,  # 끊긴 연결 자동 감지 및 재연결
}

# PostgreSQL / Supabase PgBouncer (port 6543) 최적화
# Supabase free tier PgBouncer idle timeout = 약 300초(5분).
# pool_recycle=280 으로 안전 마진 20초 확보 → race condition 방지.
engine_args.update({
    "pool_size": 3,       # 인스턴스당 기본 연결 수
    "max_overflow": 7,    # 최대 burst 연결 (총 10)
    "pool_recycle": 280,  # [FIX] 4분 40초 - PgBouncer 5분 idle timeout 이전에 재생성
    "pool_timeout": 30,   # [FIX] cold start 중 연결 대기 여유 시간 (기존 10초 → 30초)
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
