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

        # 2. Scraper Sync (Priority 2) - Only if it's "today" (offset 0)
        from datetime import timedelta
        is_today = (target_date.date() == (datetime.utcnow() + timedelta(hours=9)).date())
        
        if is_today and 'username' in creds and 'password' in creds:
            from app.scrapers.naver_ads_manager import NaverAdsManagerScraper
            scraper = NaverAdsManagerScraper()
            try:
                # [QC] Strict async handling to avoid loop conflicts
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                
                if loop and loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    data = asyncio.get_event_loop().run_until_complete(
                        scraper.get_performance_summary(creds['username'], creds['password'])
                    )
                else:
                    data = asyncio.run(scraper.get_performance_summary(creds['username'], creds['password']))
                
                if data:
                    for item in data:
                        # Find campaign and save SCRAPER metrics
                        campaign = db.query(Campaign).filter(Campaign.connection_id == conn.id, Campaign.external_id == item["id"]).first()
                        if not campaign:
                            campaign = db.query(Campaign).filter(Campaign.connection_id == conn.id, Campaign.name == item["name"]).first()
                        
                        if campaign:
                            metrics = db.query(MetricsDaily).filter(MetricsDaily.campaign_id == campaign.id, MetricsDaily.date == target_date, MetricsDaily.source == 'SCRAPER').first()
                            if not metrics:
                                metrics = MetricsDaily(id=uuid.uuid4(), campaign_id=campaign.id, date=target_date, source='SCRAPER')
                                db.add(metrics)
                            
                            metrics.spend = float(item.get("spend", 0))
                            metrics.impressions = int(item.get("impressions", 0))
                            metrics.clicks = int(item.get("clicks", 0))
                            metrics.conversions = int(item.get("conversions", 0))
                            campaign_ids_to_reconcile.add(campaign.id)
                    db.commit()
            except Exception as e:
                logger.error(f"Scraper failed for {conn.id}: {e}")
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
