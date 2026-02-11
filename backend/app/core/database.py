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

# Database Engine Configuration
connect_args = {}
engine_args = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10
}

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # SQLite doesn't support pool_size/max_overflow
    engine_args = {}

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
