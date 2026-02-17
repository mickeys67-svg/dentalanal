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

# PostgreSQL specific engine args - Enhanced for production performance
engine_args.update({
        "pool_size": 20,
        "max_overflow": 40,
        "pool_recycle": 1800, # More aggressive recycle
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
