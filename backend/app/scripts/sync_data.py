from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Keyword, PlatformType
from app.tasks.sync_data import sync_naver_data
import logging
import uuid

logger = logging.getLogger(__name__)

def sync_all_channels():
    """
    Unified entry point for multi-channel synchronization.
    Called by background tasks or management commands.
    """
    logger.info("Starting multi-channel data synchronization (Unified via Reconciliation Engine)...")
    db = SessionLocal()
    try:
        # 1. Performance Metrics & Ad Data (Reconciled)
        connections = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE").all()
        
        for conn in connections:
            logger.info(f"Triggering sync for connection: {conn.platform} (Client: {conn.client_id})")
            if conn.platform == PlatformType.NAVER_AD:
                try:
                    sync_naver_data(db, str(conn.id))
                except Exception as e:
                    logger.error(f"Naver sync failed for {conn.id}: {e}")
            elif conn.platform == PlatformType.GOOGLE_ADS:
                logger.info("Google Ads sync not yet implemented in unified pipeline.")
            elif conn.platform == PlatformType.META_ADS:
                logger.info("Meta Ads sync not yet implemented in unified pipeline.")

        # 2. Search Rank Scraping (DailyRank)
        keywords = db.query(Keyword).all()
        if not keywords:
            logger.info("No keywords found. Seeding default keywords for initial analysis.")
            for term in ["임플란트", "교정치과", "송도치과"]:
                db.add(Keyword(id=uuid.uuid4(), term=term, category="AUTO"))
            db.commit()
            keywords = db.query(Keyword).all()

        from app.worker.tasks import scrape_view_task, scrape_place_task, scrape_ad_task
        for k in keywords:
            logger.info(f"Dispatching SEO/Ranking scraper tasks for keyword: {k.term}")
            # Offload to Celery workers
            scrape_view_task.delay(k.term)
            scrape_place_task.delay(k.term)
            scrape_ad_task.delay(k.term)

    except Exception as e:
        logger.error(f"Global sync process encountered an error: {e}")
        db.rollback()
    finally:
        db.close()
    
    logger.info("All synchronization tasks dispatched successfully.")
