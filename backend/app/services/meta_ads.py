import os
from typing import List, Dict

class MetaAdsService:
    def __init__(self, access_token: str = None, ad_account_id: str = None):
        self.access_token = access_token or os.getenv("META_ADS_ACCESS_TOKEN")
        self.ad_account_id = ad_account_id or os.getenv("META_AD_ACCOUNT_ID")

    def get_campaigns(self) -> List[Dict]:
        """
        Fetch Meta Ads campaigns from Graph API (Mocked).
        """
        if not self.access_token:
            return [
                {"id": "m1", "name": "Meta_IG_임플란트_메인", "status": "ACTIVE", "budget": 45000},
                {"id": "m2", "name": "Meta_FB_치아미백_이벤트", "status": "ACTIVE", "budget": 15000}
            ]
        return []

    def get_daily_metrics(self, date: str) -> List[Dict]:
        """
        Fetch daily performance insights (Mocked).
        """
        import random
        return [
            {
                "campaign_id": "m1", 
                "clicks": random.randint(50, 150), 
                "impressions": random.randint(2000, 6000), 
                "cost": random.randint(20000, 40000), 
                "conversions": random.randint(1, 5)
            },
            {
                "campaign_id": "m2", 
                "clicks": random.randint(5, 20), 
                "impressions": random.randint(500, 1500), 
                "cost": random.randint(2000, 6000), 
                "conversions": random.randint(0, 1)
            }
        ]
