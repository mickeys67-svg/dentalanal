from sqlalchemy.orm import Session
from app.models.models import PlatformConnection, Campaign, MetricsDaily, PlatformType
from app.services.naver_ads import NaverAdsService
from app.scrapers.naver_ads_manager import NaverAdsManagerScraper
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

def sync_naver_data(db: Session, connection_id: str):
    # 1. Fetch connection details
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == connection_id).first()
    if not conn or conn.platform != PlatformType.NAVER_AD:
        logger.error(f"Invalid connection for sync: {connection_id}")
        return

    creds = conn.credentials
    
    # Use Scraping if username/password provided (Fallback strategy)
    if 'username' in creds and 'password' in creds:
        logger.info(f"Using Bright Data Scraper for connection {connection_id}")
        scraper = NaverAdsManagerScraper()
        
        # Since this is a sync function (called in background), 
        # and scraper is async, we need to run it in the event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        data = loop.run_until_complete(
            scraper.get_performance_summary(creds['username'], creds['password'])
        )
        
        if data:
            logger.info(f"Scraped {len(data)} items for connection {connection_id}")
            for item in data:
                try:
                    # 1. Get or Create Campaign
                    campaign = db.query(Campaign).filter(
                        Campaign.connection_id == conn.id,
                        Campaign.external_id == item["id"]
                    ).first()
                    
                    if not campaign:
                        import uuid
                        campaign = Campaign(
                            id=uuid.uuid4(),
                            connection_id=conn.id,
                            external_id=item["id"],
                            name=item["name"],
                            status=item.get("status", "ACTIVE")
                        )
                        db.add(campaign)
                        db.flush() # Get campaign ID
                    
                    # 2. Save Daily Metrics
                    # Check if metrics for today/yesterday already exist
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    metrics = db.query(MetricsDaily).filter(
                        MetricsDaily.campaign_id == campaign.id,
                        MetricsDaily.date == today
                    ).first()
                    
                    if not metrics:
                        import uuid
                        metrics = MetricsDaily(
                            id=uuid.uuid4(),
                            campaign_id=campaign.id,
                            date=today,
                            spend=float(item.get("spend", 0)),
                            impressions=int(item.get("impressions", 0)),
                            clicks=int(item.get("clicks", 0)),
                            conversions=int(item.get("conversions", 0))
                        )
                        db.add(metrics)
                    else:
                        # Update existing metrics
                        metrics.spend = float(item.get("spend", 0))
                        metrics.impressions = int(item.get("impressions", 0))
                        metrics.clicks = int(item.get("clicks", 0))
                        metrics.conversions = int(item.get("conversions", 0))
                        
                    db.commit()
                except Exception as item_error:
                    db.rollback()
                    logger.error(f"Failed to save item {item.get('name')}: {item_error}")
            
            logger.info(f"Finished processing {len(data)} scraped items.")
        else:
            logger.warning("Scraper returned no data.")
    
    # Original API logic (Keep as infrastructure)
    elif creds.get('customer_id') and creds.get('api_key'):
        # ... existing API logic ...
        naver = NaverAdsService(
            customer_id=creds.get('customer_id'),
            api_key=creds.get('api_key'),
            secret_key=creds.get('secret_key')
        )
        # ...
        pass

    return
