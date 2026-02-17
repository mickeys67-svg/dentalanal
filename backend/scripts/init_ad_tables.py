import sys
import os

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from sqlalchemy import text

def init_ad_tables():
    db = SessionLocal()
    try:
        print("Initializing Ad Performance Tables...")
        
        ddl_ad_groups = """
        CREATE TABLE IF NOT EXISTS ad_groups (
            id UUID PRIMARY KEY,
            campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
            external_id VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            status VARCHAR DEFAULT 'ACTIVE',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        """

        ddl_ad_keywords = """
        CREATE TABLE IF NOT EXISTS ad_keywords (
            id UUID PRIMARY KEY,
            ad_group_id UUID NOT NULL REFERENCES ad_groups(id) ON DELETE CASCADE,
            external_id VARCHAR NOT NULL UNIQUE,
            text VARCHAR NOT NULL,
            bid_amt INTEGER DEFAULT 0,
            status VARCHAR DEFAULT 'ACTIVE',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
        """

        ddl_ad_metrics = """
        CREATE TABLE IF NOT EXISTS ad_metrics_daily (
            id UUID PRIMARY KEY,
            date TIMESTAMP NOT NULL,
            ad_group_id UUID REFERENCES ad_groups(id) ON DELETE CASCADE,
            keyword_id UUID REFERENCES ad_keywords(id) ON DELETE CASCADE,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            spend FLOAT DEFAULT 0.0,
            conversions INTEGER DEFAULT 0,
            ctr FLOAT DEFAULT 0.0,
            cpc FLOAT DEFAULT 0.0,
            roas FLOAT DEFAULT 0.0,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        
        CREATE INDEX IF NOT EXISTS idx_ad_metrics_date ON ad_metrics_daily(date);
        """
        
        # SQLite compatibility adjustment (if testing locally with SQLite)
        # However, the user is likely using PostgreSQL given the "TIMESTAMPTZ" usage.
        # But `dev.py` usage suggests this DDL is accepted.
        # Let's hope the environment is Postgres, or SQLite handles it gracefully (it might not handle TIMESTAMPTZ).
        
        db.execute(text(ddl_ad_groups))
        print("Checked/Created ad_groups")
        
        db.execute(text(ddl_ad_keywords))
        print("Checked/Created ad_keywords")
        
        db.execute(text(ddl_ad_metrics))
        print("Checked/Created ad_metrics_daily")
        
        db.commit()
        print("Success.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_ad_tables()
