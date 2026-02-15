from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Campaign, MetricsDaily, User, Agency
from sqlalchemy import func

def diag():
    db = SessionLocal()
    try:
        print("=== Database Diagnosis ===")
        # 1. User & Agency
        user_count = db.query(User).count()
        agency_count = db.query(Agency).count()
        print(f"Users: {user_count}, Agencies: {agency_count}")
        
        # 2. Connections
        connections = db.query(PlatformConnection).all()
        print(f"Total Connections: {len(connections)}")
        for i, conn in enumerate(connections):
            print(f"  [{i}] ID: {conn.id}, Platform: {conn.platform}, Status: {conn.status}, Client: {conn.client_id}")
            
        # 3. Campaigns
        campaign_count = db.query(Campaign).count()
        print(f"Total Campaigns: {campaign_count}")
        
        # 4. Metrics Summary
        metrics_summary = db.query(
            MetricsDaily.source,
            func.count(MetricsDaily.id).label("count"),
            func.sum(MetricsDaily.spend).label("total_spend")
        ).group_by(MetricsDaily.source).all()
        
        print("Metrics Summary by Source:")
        if not metrics_summary:
            print("  (!) No metrics found in metrics_daily table.")
        for row in metrics_summary:
            print(f"  Source: {row.source}, Count: {row.count}, Total Spend: {row.total_spend}")
            
        # 5. Check for recent Metrics
        recent_metrics = db.query(MetricsDaily).order_by(MetricsDaily.date.desc()).limit(5).all()
        print("Recent Metrics:")
        for m in recent_metrics:
            print(f"  ID: {m.id}, Date: {m.date}, Source: {m.source}, Campaign: {m.campaign_id}")

    except Exception as e:
        print(f"Diagnosis failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diag()
