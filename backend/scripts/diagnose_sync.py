import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.models import SyncTask, PlatformConnection, Campaign, MetricsDaily, SyncValidation
from sqlalchemy import func

def diagnose():
    db = SessionLocal()
    try:
        print("=== [1] Platform Connections Status ===")
        conns = db.query(PlatformConnection).all()
        for c in conns:
            print(f"ID: {c.id} | Platform: {c.platform} | Status: {c.status}")

        print("\n=== [2] Sync Tasks Status Summary ===")
        task_stats = db.query(SyncTask.status, func.count(SyncTask.id)).group_by(SyncTask.status).all()
        for status, count in task_stats:
            print(f"Status: {status.value if hasattr(status, 'value') else status} | Count: {count}")

        print("\n=== [3] Recent Failed Tasks (Last 5) ===")
        failed_tasks = db.query(SyncTask).filter(SyncTask.status == 'FAILED').order_by(SyncTask.completed_at.desc()).limit(5).all()
        for t in failed_tasks:
            print(f"Date: {t.target_date} | Error: {t.error_message}")

        print("\n=== [4] Data Coverage (Campaigns & Metrics) ===")
        campaign_count = db.query(Campaign).count()
        metrics_count = db.query(MetricsDaily).count()
        print(f"Total Campaigns: {campaign_count}")
        print(f"Total Metrics Entries: {metrics_count}")
        
        reconciled_count = db.query(MetricsDaily).filter(MetricsDaily.source == 'RECONCILED').count()
        print(f"Reconciled Metrics Entries: {reconciled_count}")

        print("\n=== [5] Validation Results Summary ===")
        validations = db.query(SyncValidation.is_valid, func.count(SyncValidation.id)).group_by(SyncValidation.is_valid).all()
        for is_valid, count in validations:
            print(f"Is Valid: {'YES' if is_valid else 'NO'} | Count: {count}")

    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
