from app.core.database import SessionLocal
from app.tasks.sync_data import sync_naver_data
from app.models.models import PlatformConnection

def trigger_sync_manually():
    db = SessionLocal()
    try:
        # Find first NAV_AD connection
        conn = db.query(PlatformConnection).filter(PlatformConnection.platform == "NAVER_AD").first()
        if not conn:
            print("No Naver Ad connection found.")
            return
            
        print(f"Triggering sync for connection: {conn.id}")
        sync_naver_data(db, str(conn.id))
        print("Sync completed.")
        
    except Exception as e:
        print(f"Manual sync failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    trigger_sync_manually()
