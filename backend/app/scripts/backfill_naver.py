import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta
import logging

# Setup Path
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.tasks.sync_data import sync_naver_data
from app.models.models import PlatformConnection, PlatformType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_naver")

async def run_backfill(days: int, connection_id: str = None):
    db = SessionLocal()
    try:
        # Find active Naver connections
        query = db.query(PlatformConnection).filter(PlatformConnection.platform == PlatformType.NAVER_AD, PlatformConnection.status == "ACTIVE")
        if connection_id:
            query = query.filter(PlatformConnection.id == connection_id)
        
        connections = query.all()
        if not connections:
            logger.warning("No active Naver Ads connections found for backfill.")
            return

        logger.info(f"Found {len(connections)} connections. Starting deep backfill for last {days} days...")
        
        # We process in chunks to avoid overwhelming the API
        # sync_naver_data(days=X) will loop internally. 
        # But for VERY deep backfill (e.g. 60 days), we might want to do it in batches of 7 days with sleep.
        
        batch_size = 7
        for conn in connections:
            logger.info(f"Processing Connection: {conn.id} (Client: {conn.client_id})")
            remaining_days = days
            processed_days = 0
            
            while remaining_days > 0:
                current_batch = min(remaining_days, batch_size)
                # target_start_date = today - processed_days
                # sync_naver_data assumes 'today' inside. 
                # To support arbitrary historical blocks, we should ideally modify sync_naver_data to accept a base_date.
                # However, for now, we'll just pass a large 'days' count to sync_naver_data.
                
                logger.info(f"Syncing range: days={processed_days + current_batch} (Backfilling {current_batch} more days)")
                sync_naver_data(db, str(conn.id), days=(processed_days + current_batch))
                
                processed_days += current_batch
                remaining_days -= current_batch
                
                if remaining_days > 0:
                    logger.info("Batch completed. Cooling down for 5 seconds to prevent rate limits...")
                    await asyncio.sleep(5)
            
        logger.info("Deep backfill completed successfully.")
    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naver Ads Historical Data Backfill Tool")
    parser.add_argument("--days", type=int, default=30, help="Number of days to go back (default: 30)")
    parser.add_argument("--conn", type=str, help="Specific Connection ID to backfill")
    
    args = parser.parse_args()
    
    asyncio.run(run_backfill(args.days, args.conn))
