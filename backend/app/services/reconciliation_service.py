import logging
from sqlalchemy.orm import Session
from app.models.models import MetricsDaily, Campaign, PlatformType
from datetime import datetime
from typing import List, Optional
import uuid

logger = logging.getLogger(__name__)

class DataReconciliationService:
    def __init__(self, db: Session):
        self.db = db

    def reconcile_metrics(self, campaign_id: uuid.UUID, target_date: datetime):
        """
        Reconciles metrics from multiple sources for a specific campaign and date.
        Policy:
        - Spend/Clicks/Conversions: Trust API first (1.0 weight)
        - If API is missing, use Scraper data.
        - If both exist, check variance. If variance > 10%, log a warning.
        """
        sources = self.db.query(MetricsDaily).filter(
            MetricsDaily.campaign_id == campaign_id,
            MetricsDaily.date == target_date,
            MetricsDaily.source != 'RECONCILED'
        ).all()

        if not sources:
            return None

        # Sort by source priority (API > SCRAPER)
        api_data = next((s for s in sources if s.source == 'API'), None)
        scraper_data = next((s for s in sources if s.source == 'SCRAPER'), None)

        final_metrics = {
            "spend": 0.0,
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "revenue": 0.0
        }

        if api_data and scraper_data:
            # Check variance for spend
            if api_data.spend > 0:
                variance = abs(api_data.spend - scraper_data.spend) / api_data.spend
                if variance > 0.1:
                    logger.warning(f"High variance ({variance:.1%}) detected for Campaign {campaign_id} on {target_date}")

        # Final decision logic
        primary = api_data or scraper_data
        if not primary: return None

        # Populate final metrics
        final_metrics["spend"] = primary.spend
        final_metrics["impressions"] = primary.impressions
        final_metrics["clicks"] = primary.clicks
        final_metrics["conversions"] = primary.conversions
        final_metrics["revenue"] = primary.revenue

        # Create or Update RECONCILED record
        reconciled = self.db.query(MetricsDaily).filter(
            MetricsDaily.campaign_id == campaign_id,
            MetricsDaily.date == target_date,
            MetricsDaily.source == 'RECONCILED'
        ).first()

        if not reconciled:
            reconciled = MetricsDaily(
                id=uuid.uuid4(),
                campaign_id=campaign_id,
                date=target_date,
                source='RECONCILED'
            )
            self.db.add(reconciled)

        reconciled.spend = final_metrics["spend"]
        reconciled.impressions = final_metrics["impressions"]
        reconciled.clicks = final_metrics["clicks"]
        reconciled.conversions = final_metrics["conversions"]
        reconciled.revenue = final_metrics["revenue"]
        reconciled.meta_info = {
            "reconciled_at": datetime.now().isoformat(),
            "sources_used": [s.source for s in sources],
            "primary_source": primary.source
        }

        self.db.commit()
        return reconciled
