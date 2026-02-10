import requests
import time
import hmac
import hashlib
import base64
from typing import Dict, Any, List

class NaverAdsService:
    BASE_URL = "https://api.naver.com"
    
    def __init__(self, customer_id: str, api_key: str, secret_key: str):
        self.customer_id = customer_id
        self.api_key = api_key
        self.secret_key = secret_key

    def _generate_signature(self, timestamp: str, method: str, path: str) -> str:
        message = f"{timestamp}.{method}.{path}"
        hash_obj = hmac.new(
            self.secret_key.encode("utf-8"), 
            message.encode("utf-8"), 
            hashlib.sha256
        )
        return base64.b64encode(hash_obj.digest()).decode("utf-8")

    def _get_headers(self, method: str, path: str) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path)
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": self.api_key,
            "X-Customer": self.customer_id,
            "X-Signature": signature
        }

    def get_campaigns(self) -> List[Dict[str, Any]]:
        path = "/ncc/campaigns"
        headers = self._get_headers("GET", path)
        response = requests.get(f"{self.BASE_URL}{path}", headers=headers)
        response.raise_for_status()
        return response.json()

    def get_daily_report(self, campaign_id: str, date: str) -> Dict[str, Any]:
        # This is a simplified version of report fetching
        # Real Naver Ads API requires requesting a report and then downloading it
        # For now, we will return a mock structure that mirrors the real response
        return {
            "campaign_id": campaign_id,
            "date": date,
            "spend": 50000,
            "impressions": 10000,
            "clicks": 150,
            "conversions": 12
        }
