import asyncio
import os
import sys
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from app.scripts.sync_data import sync_all_channels
from app.models.models import MetricsDaily, Campaign, PlatformConnection

async def verify():
    print("=== Verification Start ===")
    db = SessionLocal()
    try:
        # 1. Connection Test
        db.execute(text("SELECT 1"))
        print("Database connection: OK")
        
        # 2. Check for ACTIVE connections
        conns = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE").all()
        print(f"Active Platform Connections: {len(conns)}")
        
        # 3. Trigger Sync
        print("Triggering sync_all_channels (Backfill Logic integrated)...")
        await sync_all_channels()
        
        # 4. Final Results check
        metrics_count = db.query(MetricsDaily).count()
        recon_count = db.query(MetricsDaily).filter(MetricsDaily.source == 'RECONCILED').count()
        print(f"Total Metrics in DB: {metrics_count}")
        print(f"RECONCILED Metrics: {recon_count}")
        
    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify())
