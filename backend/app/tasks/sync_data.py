from sqlalchemy.orm import Session
from app.models.models import PlatformConnection, Campaign, MetricsDaily, PlatformType
from app.services.naver_ads import NaverAdsService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def sync_naver_data(db: Session, connection_id: str):
    # 1. Fetch connection details
    conn = db.query(PlatformConnection).filter(PlatformConnection.id == connection_id).first()
    if not conn or conn.platform != PlatformType.NAVER_AD:
        logger.error(f"Invalid connection for sync: {connection_id}")
        return

    # 2. Initialize Service
    creds = conn.credentials
    naver = NaverAdsService(
        customer_id=creds.get('customer_id'),
        api_key=creds.get('api_key'),
        secret_key=creds.get('secret_key')
    )

    try:
        # 3. Sync Campaigns
        remote_campaigns = naver.get_campaigns()
        for rc in remote_campaigns:
            # Update or Create Campaign
            campaign = db.query(Campaign).filter(
                Campaign.connection_id == conn.id,
                Campaign.external_id == rc.get('nccCampaignId')
            ).first()

            if not campaign:
                campaign = Campaign(
                    connection_id=conn.id,
                    external_id=rc.get('nccCampaignId'),
                    name=rc.get('name'),
                    status=rc.get('status')
                )
                db.add(campaign)
                db.flush()

            # 4. Sync Daily Metrics (Mocked for now as per service method)
            # In a real scenario, this would loop through dates and handle pagination
            today = datetime.now().date()
            report = naver.get_daily_report(campaign.external_id, today.isoformat())
            
            # Save metrics
            metrics = MetricsDaily(
                campaign_id=campaign.id,
                date=datetime.now(),
                spend=report['spend'],
                impressions=report['impressions'],
                clicks=report['clicks'],
                conversions=report['conversions']
            )
            db.add(metrics)

        db.commit()
        logger.info(f"Successfully synced data for connection {connection_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to sync Naver Ads data: {str(e)}")
        raise e
