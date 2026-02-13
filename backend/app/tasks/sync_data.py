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
    # Cloud Run (us-west1) is usually UTC.
    from datetime import timedelta
    now_kst = datetime.utcnow() + timedelta(hours=9)
    today = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    
    logger.info(f"Target Sync Date (KST): {today.strftime('%Y-%m-%d')}")

    # 1. Try Scraper if credentials available
    if 'username' in creds and 'password' in creds:
        logger.info(f"Source 1: Scraping for connection {connection_id} (User: {creds.get('username')})")
        scraper = NaverAdsManagerScraper()
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        data = loop.run_until_complete(
            scraper.get_performance_summary(creds['username'], creds['password'])
        )
        
        if data:
            logger.info(f"Scraper returned {len(data)} items for {connection_id}")
            for item in data:
                try:
                    # 1단계: external_id로 조회
                    campaign = db.query(Campaign).filter(
                        Campaign.connection_id == conn.id,
                        Campaign.external_id == item["id"]
                    ).first()
                    
                    # 2단계: external_id가 다를 수 있으므로 이름으로 재조회 (Identity 매칭)
                    if not campaign:
                        campaign = db.query(Campaign).filter(
                            Campaign.connection_id == conn.id,
                            Campaign.name == item["name"]
                        ).first()
                        if campaign and not campaign.external_id:
                            logger.info(f"Campaign matched by name: {item['name']}. Updating ID to {item['id']}")
                            campaign.external_id = item["id"]
                    
                    if not campaign:
                        logger.info(f"Creating new campaign: {item['name']} ({item['id']})")
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
        else:
            logger.warning(f"Scraper returned no data for {connection_id}")

    # 2. Try Official API if credentials available
    if creds.get('customer_id') and (creds.get('api_key') or creds.get('access_license')):
        logger.info(f"Source 2: API Call for connection {connection_id} (Customer: {creds.get('customer_id')})")
        try:
            naver_service = NaverAdsService(db, credentials=conn.credentials)
            # 신규: 성과 수집 전 캠페인 목록 먼저 동기화 (Cold Start 방지)
            naver_service.sync_campaigns(conn.client_id)
            
            date_str = today.strftime("%Y-%m-%d")
            sync_count = naver_service.sync_all_campaign_metrics(conn.id, date_str)
            
            if sync_count > 0:
                logger.info(f"API sync added/updated {sync_count} metrics for {connection_id}")
                # Add all campaigns in this connection to reconciliation
                campaigns = db.query(Campaign).filter(Campaign.connection_id == conn.id).all()
                for cp in campaigns:
                    campaign_ids_to_reconcile.add(cp.id)
            else:
                logger.warning(f"API sync returned 0 results for {connection_id}")
        except Exception as api_error:
            logger.error(f"API Sync failed for {connection_id}: {api_error}")
    else:
        logger.warning(f"Skipping API sync for {connection_id}: Missing API credentials")

    # 3. Reconciliation Step
    if campaign_ids_to_reconcile:
        logger.info(f"Starting reconciliation for {len(campaign_ids_to_reconcile)} campaigns on {today.strftime('%Y-%m-%d')}...")
        from app.services.reconciliation_service import DataReconciliationService
        recon_service = DataReconciliationService(db)
        reconciled_count = 0
        for cid in campaign_ids_to_reconcile:
            res = recon_service.reconcile_metrics(cid, today)
            if res: reconciled_count += 1
        logger.info(f"Reconciliation completed for connection {connection_id}. {reconciled_count} records created/updated.")
    else:
        logger.warning(f"No campaigns to reconcile for {connection_id} (Check if API or Scraper returned any data for {today.strftime('%Y-%m-%d')})")

    return
