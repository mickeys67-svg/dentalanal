from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Cloud Run check: SQLite must use /tmp
if SQLALCHEMY_DATABASE_URL.startswith("sqlite") and os.environ.get("K_SERVICE"):
    if "./" in SQLALCHEMY_DATABASE_URL:
        # sqlite:///./test.db -> sqlite:////tmp/test.db
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("./", "/tmp/")
        import logging
        logging.info(f"Overriding SQLite path for Cloud Run: {SQLALCHEMY_DATABASE_URL}")

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

print(f"--- [DATABASE] Connecting to: {masked_url} ---")
logger.info(f"Database connection initialized: {masked_url}")

# Database Engine Configuration
connect_args = {}
engine_args = {
    "pool_pre_ping": True,
}

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL specific engine args
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
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
