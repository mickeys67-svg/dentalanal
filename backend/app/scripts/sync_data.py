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
                if 'username' in conn.credentials and 'password' in conn.credentials:
                    from app.scrapers.naver_ads_manager import NaverAdsManagerScraper
                    import asyncio
                    
                    scraper = NaverAdsManagerScraper()
                    try:
                        # Since we are in a sync function, use run_until_complete or similar
                        # This script is likely run via scheduler or CLI
                        campaigns_data = asyncio.run(scraper.get_performance_summary(
                            conn.credentials['username'], 
                            conn.credentials['password']
                        ))
                        if not campaigns_data:
                            logger.warning(f"No data scraped for {conn.client_id}")
                            campaigns_data = []
                    except Exception as e:
                        logger.error(f"Scraper failed: {e}")
                        campaigns_data = []
                else:
                    logger.warning(f"No credentials for scraping Naver for {conn.client_id}")
                    campaigns_data = []
            elif conn.platform == PlatformType.GOOGLE_ADS:
                # ... existing stubs ...
                campaigns_data = []
            
            for camp in campaigns_data:
                # Get or create campaign
                db_camp = db.query(Campaign).filter(
                    Campaign.connection_id == conn.id,
                    Campaign.external_id == camp.get("id", "SCRAPED_" + camp.get("name", "UNKNOWN"))
                ).first()
                
                if not db_camp:
                    db_camp = Campaign(
                        id=uuid.uuid4(),
                        connection_id=conn.id,
                        external_id=camp.get("id", "SCRAPED_" + camp.get("name", "UNKNOWN")),
                        name=camp["name"],
                        status=camp.get("status", "ACTIVE")
                    )
                    db.add(db_camp)
                    db.commit()
                    db.refresh(db_camp)
                
                # Fetch and save metrics
                yesterday = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                
                m_exists = db.query(MetricsDaily).filter(
                    MetricsDaily.campaign_id == db_camp.id,
                    MetricsDaily.date == yesterday
                ).first()
                
                if not m_exists:
                    metrics = MetricsDaily(
                        id=uuid.uuid4(),
                        campaign_id=db_camp.id,
                        date=yesterday,
                        spend=float(camp.get("spend", 0)),
                        impressions=int(camp.get("impressions", 0)),
                        clicks=int(camp.get("clicks", 0)),
                        conversions=int(camp.get("conversions", 0)),
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
