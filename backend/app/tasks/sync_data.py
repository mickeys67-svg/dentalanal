from sqlalchemy.orm import Session
from app.models.models import PlatformConnection, Campaign, MetricsDaily, PlatformType
from app.services.naver_ads import NaverAdsService
from app.scrapers.naver_ads_manager import NaverAdsManagerScraper
from datetime import datetime
# [IMMUTABLE CORE] 네이버 API 및 스크래퍼 정합성 수집 태스크.
import logging
import asyncio

logger = logging.getLogger(__name__)
import uuid

def sync_naver_date_metrics(db: Session, conn: PlatformConnection, target_date: datetime, task_id: str = None):
    """
    Syncs Naver Ads metrics for a SPECIFIC date/connection.
    Updated to support SyncTask tracking.
    """
    from app.services.sync_service import SyncService, VerificationService
    sync_service = SyncService(db)
    veri_service = VerificationService(db)
    
    if task_id:
        sync_service.mark_as_running(task_id)

    creds = conn.credentials
    date_str = target_date.strftime("%Y-%m-%d")
    campaign_ids_to_reconcile = set()
    error_msg = None

    try:
        from app.services.naver_ads import NaverAdsService
        # 1. API Sync
        if creds.get('customer_id') and (creds.get('api_key') or creds.get('access_license')):
            naver_service = NaverAdsService(db, credentials=conn.credentials)
            # Sync campaigns if it's "today" (roughly) or if we want fresh metadata
            if (datetime.utcnow().date() - target_date.date()).days <= 1:
                naver_service.sync_campaigns(conn.client_id)
            
            sync_count = naver_service.sync_all_campaign_metrics(conn.id, date_str)
            if sync_count > 0:
                campaigns = db.query(Campaign).filter(Campaign.connection_id == conn.id).all()
                for cp in campaigns: campaign_ids_to_reconcile.add(cp.id)

        # 2. Scraper Sync (Priority 2) - DISABLED (API ONLY STRATEGY)
        # from datetime import timedelta
        # is_today = (target_date.date() == (datetime.utcnow() + timedelta(hours=9)).date())
        
        # if is_today and 'username' in creds and 'password' in creds:
        #     # [Strategy Fix] Disable Scraper to rely on Official API only (Adriel Benchmark)
        #     pass
        #     # from app.scrapers.naver_ads_manager import NaverAdsManagerScraper
        #     # scraper = NaverAdsManagerScraper()
        #     # try:
        #     #     # ... (Scraper Logic Hidden) ...
        #     # except Exception as e:
        #     #     logger.error(f"Scraper failed for {conn.id}: {e}")
        # 3. Reconciliation for this specific date
        if campaign_ids_to_reconcile:
            from app.services.reconciliation_service import DataReconciliationService
            recon_service = DataReconciliationService(db)
            for cid in campaign_ids_to_reconcile:
                recon_service.reconcile_metrics(cid, target_date)
            
        # 4. Verification Check
        if task_id:
            veri_service.validate_sync_results(task_id)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Sync failed for {conn.id} on {date_str}: {e}")
    
    if task_id:
        sync_service.mark_as_completed(task_id, error=error_msg)
    
    return not bool(error_msg)

def sync_naver_data(db: Session, connection_id: str, days: int = None):
    # 1. Fetch connection
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == connection_id).first()
    if not conn or conn.platform != PlatformType.NAVER_AD:
        logger.error(f"Invalid connection: {connection_id}")
        return

    from app.core.config import settings
    sync_days = days or settings.SYNC_RAW_DAYS
    
    # Timezone: Naver is KST
    from datetime import timedelta
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Using the new SyncService to create tracked tasks
    from app.services.sync_service import SyncService
    sync_service = SyncService(db)
    tasks = sync_service.create_daily_tasks(connection_id, days=sync_days)
    
    logger.info(f"Created/Fetched {len(tasks)} sync tasks for connection {connection_id}")
    
    for task in tasks:
        logger.info(f"Processing Task {task.id} for date {task.target_date}")
        sync_naver_date_metrics(db, conn, task.target_date, task_id=str(task.id))

    return

async def sync_all_channels(db: Session, client_id: str = None, days: int = None):
    """
    Unified ASYNC entry point for multi-channel synchronization.
    If client_id is provided, only sync for that specific advertiser.
    If days is provided, sync for that many past days.
    """
    if client_id:
        logger.info(f"=== Starting Async Data Sync Routine for Client: {client_id} (Days: {days}) ===")
    else:
        logger.info(f"=== Starting Async Robust Multi-Channel Data Sync Routine (Days: {days}) ===")
    
    try:
        # 1. Platform Performance Metrics (Supabase Tracked)
        query = db.query(PlatformConnection).filter(PlatformConnection.status == "ACTIVE")
        if client_id:
            query = query.filter(PlatformConnection.client_id == client_id)
        connections = query.all()
        
        from app.services.sync_service import SyncService
        sync_service = SyncService(db)
        
        for conn in connections:
            try:
                logger.info(f"-> Scheduling tracked sync for connection: {conn.platform} (ID: {conn.id})")
                if conn.platform == PlatformType.NAVER_AD:
                    # SyncService will create PENDING tasks for the backfill period
                    sync_naver_data(db, str(conn.id), days=days)
                    logger.info(f"Tracked sync cycle initiated for Naver Ads {conn.id}")
                elif conn.platform == PlatformType.GOOGLE_ADS:
                    logger.info(f"Google Ads sync skipped (Pending implementation) for {conn.id}")
            except Exception as conn_error:
                logger.error(f"!!! Error initiating sync for connection {conn.id}: {conn_error}")
                continue

        # 2. SEO/Search Rank Scraping (DailyRank)
        from app.models.models import Keyword
        keywords = db.query(Keyword).all()
        if not keywords:
            logger.info("No keywords found. Skipping scraping.")
        else:
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
                
                try:
                    # 1. Place & View Scraping (Async)
                    place_task = run_place_scraper(k.term)
                    view_task = run_view_scraper(k.term)
                    
                    place_results, view_results = await asyncio.gather(place_task, view_task, return_exceptions=True)
                    
                    if not isinstance(place_results, Exception):
                        p_count = len(place_results)
                        stats["place"] += p_count
                        service.save_place_results(k.term, place_results)
                    else:
                        error_logs.append(f"Place({k.term}): {str(place_results)}")

                    if not isinstance(view_results, Exception):
                        v_count = len(view_results)
                        stats["view"] += v_count
                        service.save_view_results(k.term, view_results)
                    else:
                        error_logs.append(f"View({k.term}): {str(view_results)}")

                    # 2. Ad Scraping (Async)
                    try:
                        ad_results = await ad_scraper.get_ad_rankings(k.term)
                        a_count = len(ad_results) if ad_results else 0
                        stats["ad"] += a_count
                        if ad_results:
                            service.save_ad_results(k.term, ad_results)
                    except Exception as ad_err:
                         error_logs.append(f"Ad({k.term}): {str(ad_err)}")

                except Exception as e:
                    error_logs.append(f"Batch({k.term}): {str(e)}")
                    logger.error(f"Scraper batch failed for '{k.term}': {e}")

            # Notify Completion
            try:
                from app.models.models import User, UserRole, Notification
                admins = db.query(User).filter(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])).all()
                
                summary_text = f"수집 결과: 플레이스 {stats['place']}건, VIEW {stats['view']}건, 광고 {stats['ad']}건.\n"
                if error_logs:
                    err_text = "\n".join(error_logs[:3])
                    if len(error_logs) > 3: err_text += f"\n...외 {len(error_logs)-3}건"
                    summary_text += f"\n[오류 발생]\n{err_text}"
                
                msg_title = "데이터 동기화 완료"
                msg_content = f"전체 데이터 동기화 작업이 완료되었습니다.\n{summary_text}"
                
                for admin in admins:
                    db.add(Notification(
                        id=uuid.uuid4(),
                        user_id=admin.id,
                        title=msg_title,
                        content=msg_content,
                        type="NOTICE",
                        is_read=0
                    ))
                db.commit()
            except Exception as notify_err:
                logger.error(f"Failed to send completion notification: {notify_err}")

    except Exception as e:
        logger.error(f"CRITICAL: Global sync process encountered a fatal error: {e}")
    
    logger.info("=== Async Robust Synchronization Routine Completed ===")

def run_sync_process(db: Session, client_id: str = None, days: int = None):
    """
    Synchronous wrapper to run the async sync process.
    """
    try:
        asyncio.run(sync_all_channels(db, client_id, days))
    except Exception as e:
        logger.error(f"Sync process wrapper failed: {e}")


