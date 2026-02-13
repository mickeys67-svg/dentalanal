from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Campaign, MetricsDaily
from sqlalchemy import func

def check_db_state():
    db = SessionLocal()
    try:
        conn_count = db.query(PlatformConnection).count()
        campaign_count = db.query(Campaign).count()
        metrics_by_source = db.query(MetricsDaily.source, func.count(MetricsDaily.id)).group_by(MetricsDaily.source).all()
        
        print(f"Connections: {conn_count}")
        print(f"Campaigns: {campaign_count}")
        print("Metrics by Source:")
        for source, count in metrics_by_source:
            print(f"  - {source}: {count}")
            
        # Check latest metrics
        latest = db.query(MetricsDaily).order_by(MetricsDaily.date.desc()).limit(5).all()
        print("\nLatest 5 Metrics:")
        for m in latest:
            print(f"  Date: {m.date}, Campaign: {m.campaign_id}, Source: {m.source}, Spend: {m.spend}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_db_state()
