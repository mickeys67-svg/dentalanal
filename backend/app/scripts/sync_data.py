import logging
import asyncio
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Keyword, PlatformType

logger = logging.getLogger(__name__)

async def sync_all_channels():
    """
    Unified ASYNC entry point for multi-channel synchronization.
    Called by background tasks, management commands, or Cloud Scheduler.
    Ensures data persistence even if some tasks fail.
    """
    logger.info("=== Starting Async Robust Multi-Channel Data Sync Routine ===")
    
    # We use a context manager for DB session to ensure closure
    db = SessionLocal()
    try:
        # 1. Platform Performance Metrics (Supabase + MongoDB)
        connections = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE").all()
        
        # We'll import inside to avoid circular deps if any
        from app.tasks.sync_data import sync_naver_data
        
        for conn in connections:
            try:
                logger.info(f"-> Syncing connection: {conn.platform} (ID: {conn.id}, Client: {conn.client_id})")
                if conn.platform == PlatformType.NAVER_AD:
                    # sync_naver_data is now expected to be handled or updated for async safety
                    # For now, keeping it sync but wrapping if needed. Or making it async later.
                    # Since it uses requests, we'll keep it as is but careful with loops.
                    sync_naver_data(db, str(conn.id))
                    logger.info(f"Successfully synced Naver Ads for {conn.id}")
                elif conn.platform == PlatformType.GOOGLE_ADS:
                    logger.info(f"Google Ads sync skipped (Pending implementation) for {conn.id}")
            except Exception as conn_error:
                logger.error(f"!!! Failed to sync connection {conn.id}: {conn_error}")
                db.rollback()
                continue

        # 2. SEO/Search Rank Scraping (DailyRank)
        keywords = db.query(Keyword).all()
        if not keywords:
            logger.info("No keywords found. Seeding default keywords.")
            seed_terms = ["임플란트", "교정치과", "송도치과"]
            for term in seed_terms:
                if not db.query(Keyword).filter(Keyword.term == term).first():
                    db.add(Keyword(id=uuid.uuid4(), term=term, category="AUTO"))
            db.commit()
            keywords = db.query(Keyword).all()

        # Import scrapers directly to bypass Celery worker dependency
        from app.worker.tasks import run_place_scraper, run_view_scraper
        from app.scrapers.naver_ad import NaverAdScraper
        from app.services.analysis import AnalysisService
        
        service = AnalysisService(db)
        ad_scraper = NaverAdScraper()

        for k in keywords:
            logger.info(f"-> Executing SEO/Ranking scraper tasks for keyword: {k.term}")
            
            # Use asyncio.gather for parallel scraping within each keyword to improve speed
            try:
                # 1. Place & View Scraping (Async)
                place_task = run_place_scraper(k.term)
                view_task = run_view_scraper(k.term)
                
                place_results, view_results = await asyncio.gather(place_task, view_task, return_exceptions=True)
                
                # Handling results safely
                if not isinstance(place_results, Exception):
                    service.save_place_results(k.term, place_results)
                    logger.info(f"VIEW rank sync completed for '{k.term}'")
                else:
                    logger.error(f"PLACE sync error for {k.term}: {place_results}")

                if not isinstance(view_results, Exception):
                    service.save_view_results(k.term, view_results)
                    logger.info(f"VIEW rank sync completed for '{k.term}'")
                else:
                    logger.error(f"VIEW sync error for {k.term}: {view_results}")

                # 2. Ad Scraping (Async)
                ad_results = await ad_scraper.get_ad_rankings(k.term)
                service.save_ad_results(k.term, ad_results)
                logger.info(f"AD rank sync completed for '{k.term}'")

            except Exception as e:
                logger.error(f"Scraper batch failed for '{k.term}': {e}")

    except Exception as e:
        logger.error(f"CRITICAL: Global sync process encountered a fatal error: {e}")
    finally:
        db.close()
    
    logger.info("=== Async Robust Synchronization Routine Completed ===")
