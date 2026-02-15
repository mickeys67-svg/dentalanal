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

def sync_naver_data(db: Session, connection_id: str):
    # 1. Fetch connection details
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == connection_id).first()
    if not conn or conn.platform != PlatformType.NAVER_AD:
        logger.error(f"Invalid connection for sync: {connection_id}")
        return

    creds = conn.credentials
    
    # --- Dual Source Collection & Reconciliation ---
    campaign_ids_to_reconcile = set()
    
    # Timezone correction: Naver is KST (UTC+9). 
    from datetime import timedelta
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    
    logger.info(f"Target Sync Date (KST): {today.strftime('%Y-%m-%d')}")

    # 1. Try Official API first (Priority 1)
    if creds.get('customer_id') and (creds.get('api_key') or creds.get('access_license')):
        logger.info(f"Priority 1: API Call for connection {connection_id} (Customer: {creds.get('customer_id')})")
        try:
            naver_service = NaverAdsService(db, credentials=conn.credentials)
            # 캠페인 목록 동기화 (Identity 확보)
            naver_service.sync_campaigns(conn.client_id)
            
            date_str = today.strftime("%Y-%m-%d")
            sync_count = naver_service.sync_all_campaign_metrics(conn.id, date_str)
            
            if sync_count > 0:
                logger.info(f"API sync added/updated {sync_count} metrics for {connection_id}")
                campaigns = db.query(Campaign).filter(Campaign.connection_id == conn.id).all()
                for cp in campaigns:
                    campaign_ids_to_reconcile.add(cp.id)
            else:
                logger.warning(f"API sync returned 0 results for {connection_id}")
        except Exception as api_error:
            logger.error(f"API Sync failed for {connection_id}: {api_error}")
    else:
        logger.warning(f"Skipping API sync for {connection_id}: Missing API credentials")

    # 2. Try Scraper for missing or supplemental data (Priority 2)
    if 'username' in creds and 'password' in creds:
        logger.info(f"Priority 2: Scraping for connection {connection_id} (User: {creds.get('username')})")
        scraper = NaverAdsManagerScraper()
        
        try:
            # Check if we are already in an async loop (likely)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # If loop is running, we cannot use run_until_complete.
                # Since this function is sync, we need an entry point.
                # However, in dentalanal, this sync_naver_data is called within an async task.
                # WE RECOMMEND renaming this to async def, but for a quick fix:
                import nest_asyncio
                nest_asyncio.apply()
                data = asyncio.get_event_loop().run_until_complete(
                    scraper.get_performance_summary(creds['username'], creds['password'])
                )
            else:
                data = asyncio.run(scraper.get_performance_summary(creds['username'], creds['password']))
        except Exception as e:
            logger.error(f"Scraper item parsing error: {e}")
            data = None
        
        if data:
            logger.info(f"Scraper returned {len(data)} items for {connection_id}")
            for item in data:
                try:
                    # 1단계: external_id로 조회 (API에서 생성한 캠페인과 매칭)
                    campaign = db.query(Campaign).filter(
                        Campaign.connection_id == conn.id,
                        Campaign.external_id == item["id"]
                    ).first()
                    
                    # 2단계: 이름 매칭 (API 실패 시 대비)
                    if not campaign:
                        campaign = db.query(Campaign).filter(
                            Campaign.connection_id == conn.id,
                            Campaign.name == item["name"]
                        ).first()
                    
                    if not campaign:
                        logger.info(f"Creating new campaign target via Scraper: {item['name']}")
                        campaign = Campaign(id=uuid.uuid4(), connection_id=conn.id, external_id=item["id"], name=item["name"])
                        db.add(campaign)
                        db.flush()
                    
                    # Save as SCRAPER source
                    metrics = db.query(MetricsDaily).filter(
                        MetricsDaily.campaign_id == campaign.id,
                        MetricsDaily.date == today,
                        MetricsDaily.source == 'SCRAPER'
                    ).first()
                    
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
        # Default to 7 days if not configured
        backfill_days = getattr(settings, "SYNC_BACKFILL_DAYS", 7)
        logger.info(f"Starting reconciliation backfill for last {backfill_days} days...")
        from app.services.reconciliation_service import DataReconciliationService
        recon_service = DataReconciliationService(db)
        
        # Loop through configured days (including today)
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
