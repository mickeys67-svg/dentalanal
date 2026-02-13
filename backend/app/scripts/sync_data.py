from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Keyword, PlatformType
from app.tasks.sync_data import sync_naver_data
import logging
import uuid

logger = logging.getLogger(__name__)

def sync_all_channels():
    """
    Unified entry point for multi-channel synchronization.
    Called by background tasks, management commands, or Cloud Scheduler.
    Ensures data persistence even if some tasks fail.
    """
    logger.info("=== Starting Robust Multi-Channel Data Sync Routine ===")
    db = SessionLocal()
    try:
        # 1. Platform Performance Metrics (Supabase + MongoDB)
        # We fetch active connections and sync them one by one.
        connections = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE").all()
        
        for conn in connections:
            try:
                logger.info(f"-> Syncing connection: {conn.platform} (ID: {conn.id}, Client: {conn.client_id})")
                if conn.platform == PlatformType.NAVER_AD:
                    # sync_naver_data includes internal reconciliation and persistence (Supabase + MongoDB)
                    sync_naver_data(db, str(conn.id))
                    logger.info(f"Successfully synced Naver Ads for {conn.id}")
                elif conn.platform == PlatformType.GOOGLE_ADS:
                    logger.info(f"Google Ads sync skipped (Pending implementation) for {conn.id}")
                elif conn.platform == PlatformType.META_ADS:
                    logger.info(f"Meta Ads sync skipped (Pending implementation) for {conn.id}")
            except Exception as conn_error:
                logger.error(f"!!! Failed to sync connection {conn.id}: {conn_error}")
                db.rollback() # Rollback current connection's failures to keep session clean
                continue # Proceed to next connection

        # 2. SEO/Search Rank Scraping (DailyRank)
        # These are keyword-based and don't require external API credentials necessarily
        keywords = db.query(Keyword).all()
        if not keywords:
            logger.info("No keywords found. Seeding default keywords for initial system check.")
            seed_terms = ["임플란트", "교정치과", "송도치과"]
            for term in seed_terms:
                if not db.query(Keyword).filter(Keyword.term == term).first():
                    db.add(Keyword(id=uuid.uuid4(), term=term, category="AUTO"))
            db.commit()
            keywords = db.query(Keyword).all()

        from app.worker.tasks import execute_view_sync, execute_place_sync, execute_ad_sync
        
        for k in keywords:
            logger.info(f"-> Executing SEO/Ranking scraper tasks for keyword: {k.term}")
            # Each sync is isolated to prevent one failure from stopping the whole routine
            try:
                execute_view_sync(k.term)
                logger.info(f"VIEW rank sync completed for '{k.term}'")
            except Exception as e:
                logger.error(f"VIEW sync failed for '{k.term}': {e}")

            try:
                execute_place_sync(k.term)
                logger.info(f"PLACE rank sync completed for '{k.term}'")
            except Exception as e:
                logger.error(f"PLACE sync failed for '{k.term}': {e}")

            try:
                execute_ad_sync(k.term)
                logger.info(f"AD rank sync completed for '{k.term}'")
            except Exception as e:
                logger.error(f"AD sync failed for '{k.term}': {e}")

    except Exception as e:
        logger.error(f"CRITICAL: Global sync process encountered a fatal error: {e}")
    finally:
        db.close()
    
    logger.info("=== Robust Synchronization Routine Completed ===")
