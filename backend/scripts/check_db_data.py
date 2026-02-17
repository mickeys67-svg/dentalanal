
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:2KJCvEbTrWjAjXH1@db.xklppnykoeezgtxmomrl.supabase.co:5432/postgres?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    db = SessionLocal()
    try:
        # Table counts
        metrics_count = db.execute(text("SELECT count(*) FROM metrics_daily")).fetchone()[0]
        reconciled_count = db.execute(text("SELECT count(*) FROM metrics_daily WHERE source = 'RECONCILED'")).fetchone()[0]
        campaigns_count = db.execute(text("SELECT count(*) FROM campaigns")).fetchone()[0]
        connections_count = db.execute(text("SELECT count(*) FROM platform_connections")).fetchone()[0]
        clients_count = db.execute(text("SELECT count(*) FROM clients")).fetchone()[0]
        
        print(f"Metrics count: {metrics_count}")
        print(f"Metrics (RECONCILED) count: {reconciled_count}")
        print(f"Campaigns count: {campaigns_count}")
        print(f"Connections count: {connections_count}")
        print(f"Clients count: {clients_count}")
        
        if metrics_count > 0:
            print("\nSample sources in metrics_daily:")
            sources = db.execute(text("SELECT DISTINCT source FROM metrics_daily")).fetchall()
            for s in sources:
                print(f"- {s[0]}")
                
        if reconciled_count > 0:
            print("\nSample RECONCILED data:")
            sample = db.execute(text("SELECT * FROM metrics_daily WHERE source = 'RECONCILED' LIMIT 1")).fetchone()
            print(sample)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
