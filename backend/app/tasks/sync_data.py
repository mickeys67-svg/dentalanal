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

def sync_naver_data(db: Session, connection_id: str, days: int = None):
    # 1. Fetch connection details
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == connection_id).first()
    if not conn or conn.platform != PlatformType.NAVER_AD:
        logger.error(f"Invalid connection for sync: {connection_id}")
        return

    creds = conn.credentials
    from app.core.config import settings
    sync_days = days or settings.SYNC_RAW_DAYS
    
    # --- Dual Source Collection & Reconciliation ---
    campaign_ids_to_reconcile = set()
    
    # Timezone correction: Naver is KST (UTC+9). 
    from datetime import timedelta
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    
    logger.info(f"Target Sync Windows: Last {sync_days} days starting from {today.strftime('%Y-%m-%d')}")

    # --- RAW DATA COLLECTION LOOP ---
    for d_offset in range(sync_days):
        target_date = today - timedelta(days=d_offset)
        date_str = target_date.strftime("%Y-%m-%d")

        # 1. Try Official API first (Priority 1)
        if creds.get('customer_id') and (creds.get('api_key') or creds.get('access_license')):
            try:
                naver_service = NaverAdsService(db, credentials=conn.credentials)
                if d_offset == 0: # 캠페인 목록은 오늘 기준으로 한번만 동기화
                    naver_service.sync_campaigns(conn.client_id)
                
                sync_count = naver_service.sync_all_campaign_metrics(conn.id, date_str)
                if sync_count > 0:
                    campaigns = db.query(Campaign).filter(Campaign.connection_id == conn.id).all()
                    for cp in campaigns: campaign_ids_to_reconcile.add(cp.id)
            except Exception as e:
                logger.error(f"API Sync failed for {date_str}: {e}")

        # 2. Try Scraper (Priority 2) - 현재 스크래퍼는 '오늘' 성과 요약 중심이므로 d_offset == 0 일때만 실행
        if d_offset == 0 and 'username' in creds and 'password' in creds:
            scraper = NaverAdsManagerScraper()
            try:
                # Check if we are already in an async loop
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
            except Exception as e:
                logger.error(f"Scraper execution error: {e}")
                data = None
            
            if data:
                logger.info(f"Scraper returned {len(data)} items for today")
                for item in data:
                    try:
                        campaign = db.query(Campaign).filter(Campaign.connection_id == conn.id, Campaign.external_id == item["id"]).first()
                        if not campaign:
                            campaign = db.query(Campaign).filter(Campaign.connection_id == conn.id, Campaign.name == item["name"]).first()
                        
                        if not campaign:
                            campaign = Campaign(id=uuid.uuid4(), connection_id=conn.id, external_id=item["id"], name=item["name"])
                            db.add(campaign)
                            db.flush()
                        
                        metrics = db.query(MetricsDaily).filter(MetricsDaily.campaign_id == campaign.id, MetricsDaily.date == today, MetricsDaily.source == 'SCRAPER').first()
                        if not metrics:
                            metrics = MetricsDaily(id=uuid.uuid4(), campaign_id=campaign.id, date=today, source='SCRAPER')
                            db.add(metrics)
                        
                        metrics.spend = float(item.get("spend", 0))
                        metrics.impressions = int(item.get("impressions", 0))
                        metrics.clicks = int(item.get("clicks", 0))
                        metrics.conversions = int(item.get("conversions", 0))
                        campaign_ids_to_reconcile.add(campaign.id)
                    except Exception as e:
                        logger.error(f"Scraper item parsing error: {e}")
                db.commit()

    # 3. Reconciliation Step (Backfill last N days)
    if campaign_ids_to_reconcile:
        backfill_days = getattr(settings, "SYNC_BACKFILL_DAYS", 7)
        logger.info(f"Starting reconciliation backfill for last {backfill_days} days...")
        from app.services.reconciliation_service import DataReconciliationService
        recon_service = DataReconciliationService(db)
        
        for d_offset in range(backfill_days):
            target_date = today - timedelta(days=d_offset)
            reconciled_count = 0
            for cid in campaign_ids_to_reconcile:
                res = recon_service.reconcile_metrics(cid, target_date)
                if res: reconciled_count += 1
            if reconciled_count > 0:
                logger.info(f"Finalized {reconciled_count} records for {target_date.strftime('%Y-%m-%d')}")
    else:
        logger.warning(f"No campaigns to reconcile for {connection_id}")
    return
