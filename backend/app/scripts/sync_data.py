from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Campaign, MetricsDaily, Keyword, PlatformType
from app.services.naver_ads import NaverAdsService
from app.services.google_ads import GoogleAdsService
from app.services.meta_ads import MetaAdsService
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

def sync_all_channels():
    logger.info("Starting multi-channel data synchronization...")
    db = SessionLocal()
    try:
        # 1. Fetch all active connections
        connections = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE").all()
        
        for conn in connections:
            logger.info(f"Syncing connection: {conn.platform} for client: {conn.client_id}")
            
            campaigns_data = []
            if conn.platform == PlatformType.NAVER_AD:
                # Stub: In real app, use conn.credentials
                service = NaverAdsService(customer_id="stub", api_key="stub", secret_key="stub")
                campaigns_data = [{"id": "n1", "name": "네이버 브랜드검색_치과", "status": "ACTIVE"}]
            elif conn.platform == PlatformType.GOOGLE_ADS:
                service = GoogleAdsService()
                campaigns_data = service.get_campaigns(customer_id="stub")
            elif conn.platform == PlatformType.META_ADS:
                service = MetaAdsService()
                campaigns_data = service.get_campaigns()

            for camp in campaigns_data:
                # Get or create campaign
                db_camp = db.query(Campaign).filter(
                    Campaign.connection_id == conn.id,
                    Campaign.external_id == camp["id"]
                ).first()
                
                if not db_camp:
                    db_camp = Campaign(
                        id=uuid.uuid4(),
                        connection_id=conn.id,
                        external_id=camp["id"],
                        name=camp["name"],
                        status=camp.get("status", "ACTIVE")
                    )
                    db.add(db_camp)
                    db.commit()
                    db.refresh(db_camp)
                
                # Fetch and save metrics for last 7 days (simplified)
                yesterday = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Check if metrics already exist for yesterday
                m_exists = db.query(MetricsDaily).filter(
                    MetricsDaily.campaign_id == db_camp.id,
                    MetricsDaily.date == yesterday
                ).first()
                
                if not m_exists:
                    # Mock specific metrics based on platform
                    import random
                    metrics = MetricsDaily(
                        id=uuid.uuid4(),
                        campaign_id=db_camp.id,
                        date=yesterday,
                        spend=random.uniform(10000, 50000),
                        impressions=random.randint(1000, 5000),
                        clicks=random.randint(50, 200),
                        conversions=random.randint(1, 10),
                        revenue=0.0
                    )
                    db.add(metrics)
        
        db.commit()

        # 2. Trigger Scraping Tasks
        keywords = db.query(Keyword).all()
        if not keywords:
            logger.info("No keywords found. Seeding default keywords.")
            for term in ["임플란트", "교정치과", "송도치과"]:
                db.add(Keyword(id=uuid.uuid4(), term=term, category="AUTO"))
            db.commit()
            keywords = db.query(Keyword).all()

        from app.worker.tasks import scrape_view_task, scrape_place_task, scrape_ad_task
        for k in keywords:
            logger.info(f"Dispatching scraper tasks for: {k.term}")
            scrape_view_task.delay(k.term)
            scrape_place_task.delay(k.term)
            scrape_ad_task.delay(k.term)

    except Exception as e:
        logger.error(f"Sync process failed: {e}")
        db.rollback()
    finally:
        db.close()
    
    logger.info("Data synchronization finished.")
