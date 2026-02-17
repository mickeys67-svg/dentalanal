import sys
import os
import uuid
from datetime import datetime

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.services.naver_ads import NaverAdsService
from app.models.models import PlatformConnection, PlatformType, AdGroup, AdKeyword, AdMetricsDaily

def verify_sync():
    db = SessionLocal()
    try:
        print("Starting Verification...")
        
        # 1. Find a valid connection
        connection = db.query(PlatformConnection).filter(
            PlatformConnection.platform == PlatformType.NAVER_AD,
            PlatformConnection.status == 'ACTIVE'
        ).first()
        
        if not connection:
            print("No active NAVER_AD connection found. Skipping real sync test.")
            return

        print(f"Found Connection: {connection.account_id}")
        
        # 2. Initialize Service
        service = NaverAdsService(db)
        
        # 3. Run Sync (for today)
        today_str = datetime.now().strftime("%Y-%m-%d")
        print(f"Syncing metrics for {today_str}...")
        
        try:
            count = service.sync_all_campaign_metrics(connection.id, today_str)
            print(f"Sync Complete. Processed {count} items (keywords/metrics).")
            
            # 4. Verify DB Content
            ad_groups = db.query(AdGroup).count()
            keywords = db.query(AdKeyword).count()
            metrics = db.query(AdMetricsDaily).count()
            
            print(f"DB Status:")
            print(f" - AdGroups: {ad_groups}")
            print(f" - Keywords: {keywords}")
            print(f" - Metrics: {metrics}")
            
        except Exception as e:
            print(f"Sync Failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_sync()
