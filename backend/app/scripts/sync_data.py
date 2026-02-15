import logging
import asyncio
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import PlatformConnection, Keyword, PlatformType

logger = logging.getLogger(__name__)

async def sync_all_channels(client_id: str = None, days: int = None):
    """
    Unified ASYNC entry point for multi-channel synchronization.
    If client_id is provided, only sync for that specific advertiser.
    If days is provided, sync for that many past days.
    """
    if client_id:
        logger.info(f"=== Starting Async Data Sync Routine for Client: {client_id} (Days: {days}) ===")
    else:
        logger.info(f"=== Starting Async Robust Multi-Channel Data Sync Routine (Days: {days}) ===")
    
    # We use a context manager for DB session to ensure closure
    db = SessionLocal()
    try:
        # 1. Platform Performance Metrics (Supabase Tracked)
        query = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE")
        if client_id:
            query = query.filter(PlatformConnection.client_id == client_id)
        connections = query.all()
        
        from app.services.sync_service import SyncService
        from app.tasks.sync_data import sync_naver_data
        sync_service = SyncService(db)
        
        for conn in connections:
            try:
                logger.info(f"-> Scheduling tracked sync for connection: {conn.platform} (ID: {conn.id})")
                if conn.platform == PlatformType.NAVER_AD:
                    # SyncService will create PENDING tasks for the backfill period
                    # sync_naver_data will correctly process these tasks through the new architecture
                    sync_naver_data(db, str(conn.id), days=days)
                    logger.info(f"Tracked sync cycle initiated for Naver Ads {conn.id}")
                elif conn.platform == PlatformType.GOOGLE_ADS:
                    logger.info(f"Google Ads sync skipped (Pending implementation) for {conn.id}")
            except Exception as conn_error:
                logger.error(f"!!! Error initiating sync for connection {conn.id}: {conn_error}")
                continue

        # 2. SEO/Search Rank Scraping (DailyRank)
        keywords = db.query(Keyword).all()
        if not keywords:
            logger.info("No keywords found. Skipping default seeding to avoid 'hidden' automatic data.")
            # seed_terms = ["임플란트", "교정치과", "송도치과"]
            # for term in seed_terms:
            #     if not db.query(Keyword).filter(Keyword.term == term).first():
            #         db.add(Keyword(id=uuid.uuid4(), term=term, category="AUTO"))
            # db.commit()
            # keywords = db.query(Keyword).all()

        # Import scrapers directly to bypass Celery worker dependency
        from app.worker.tasks import run_place_scraper, run_view_scraper
        from app.scrapers.naver_ad import NaverAdScraper
        from app.services.analysis import AnalysisService
        
        service = AnalysisService(db)
        ad_scraper = NaverAdScraper()

        # Stats tracking
        stats = {"place": 0, "view": 0, "ad": 0}
        error_logs = []

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
                    p_count = len(place_results)
                    stats["place"] += p_count
                    service.save_place_results(k.term, place_results)
                    logger.info(f"PLACE sync completed for '{k.term}' ({p_count} items)")
                else:
                    error_logs.append(f"Place({k.term}): {str(place_results)}")
                    logger.error(f"PLACE sync error for {k.term}: {place_results}")

                if not isinstance(view_results, Exception):
                    v_count = len(view_results)
                    stats["view"] += v_count
                    service.save_view_results(k.term, view_results)
                    logger.info(f"VIEW sync completed for '{k.term}' ({v_count} items)")
                else:
                    error_logs.append(f"View({k.term}): {str(view_results)}")
                    logger.error(f"VIEW sync error for {k.term}: {view_results}")

                # 2. Ad Scraping (Async)
                try:
                    ad_results = await ad_scraper.get_ad_rankings(k.term)
                    a_count = len(ad_results) if ad_results else 0
                    stats["ad"] += a_count
                    if ad_results:
                        service.save_ad_results(k.term, ad_results)
                    logger.info(f"AD rank sync completed for '{k.term}' ({a_count} items)")
                except Exception as ad_err:
                     error_logs.append(f"Ad({k.term}): {str(ad_err)}")
                     logger.error(f"AD sync error for {k.term}: {ad_err}")

            except Exception as e:
                error_logs.append(f"Batch({k.term}): {str(e)}")
                logger.error(f"Scraper batch failed for '{k.term}': {e}")

    except Exception as e:
        logger.error(f"CRITICAL: Global sync process encountered a fatal error: {e}")
    finally:
        db.close()
        
        # Create Completion Notification with Fresh Session
        notify_db = SessionLocal()
        try:
            from app.models.models import User, UserRole, Notification
            # Ensure session is active
            admins = notify_db.query(User).filter(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])).all()
            
            summary_text = (
                f"수집 결과: 플레이스 {stats['place']}건, VIEW {stats['view']}건, 광고 {stats['ad']}건.\n"
            )
            if error_logs:
                # Truncate errors if too long
                err_text = "\n".join(error_logs[:3])
                if len(error_logs) > 3: err_text += f"\n...외 {len(error_logs)-3}건"
                summary_text += f"\n[오류 발생]\n{err_text}"
            
            msg_title = "데이터 동기화 완료"
            msg_content = "전체 데이터 동기화 작업이 완료되었습니다.\n" + summary_text
            
            if client_id:
                msg_content = f"광고주({client_id}) 데이터 동기화 완료.\n" + summary_text
            
            for admin in admins:
                note = Notification(
                    id=uuid.uuid4(),
                    user_id=admin.id,
                    title=msg_title,
                    content=msg_content,
                    type="NOTICE",
                    is_read=0
                )
                notify_db.add(note)
            notify_db.commit()
        except Exception as notify_err:
            logger.error(f"Failed to send completion notification: {notify_err}")
        finally:
            notify_db.close()
    
    logger.info("=== Async Robust Synchronization Routine Completed ===")

def run_sync_process(client_id: str = None, days: int = None):
    """
    Synchronous wrapper to run the async sync process in a background thread.
    Ideal for BackgroundTasks in FastAPI.
    """
    try:
        logging.getLogger(__name__).info(f"Starting sync process for client {client_id}")
        asyncio.run(sync_all_channels(client_id, days))
    except Exception as e:
        logging.getLogger(__name__).error(f"Sync process wrapper failed: {e}")
