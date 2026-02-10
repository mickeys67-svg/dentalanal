import os
from typing import List, Dict

class GoogleAdsService:
    def __init__(self, developer_token: str = None, client_id: str = None, client_secret: str = None):
        self.developer_token = developer_token or os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.client_id = client_id or os.getenv("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_ADS_CLIENT_SECRET")

    def get_campaigns(self, customer_id: str) -> List[Dict]:
        """
        Fetch Google Ads campaigns using Google Ads API (Mocked).
        """
        if not self.developer_token or customer_id == "stub":
            return [
                {"id": "g1", "name": "Google 검색_브랜드", "status": "ENABLED", "budget": 100000},
                {"id": "g2", "name": "Google 디스플레이_관심사", "status": "ENABLED", "budget": 50000}
            ]
        
        # Real logic would use the google-ads client here
        return []

    def get_daily_metrics(self, customer_id: str, date: str) -> List[Dict]:
        """
        Fetch daily performance metrics (Mocked).
        """
        import random
        return [
            {
                "campaign_id": "g1", 
                "clicks": random.randint(100, 300), 
                "impressions": random.randint(5000, 10000), 
                "cost": random.randint(30000, 80000), 
                "conversions": random.randint(2, 8)
            },
            {
                "campaign_id": "g2", 
                "clicks": random.randint(10, 50), 
                "impressions": random.randint(1000, 3000), 
                "cost": random.randint(5000, 15000), 
                "conversions": random.randint(0, 2)
            }
        ]
