import time
import hashlib
import hmac
import base64
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import PlatformConnection, Campaign, MetricsDaily, PlatformType
import logging

logger = logging.getLogger(__name__)

class NaverAdsService:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://api.searchad.naver.com"
        self.customer_id = settings.NAVER_AD_CUSTOMER_ID
        self.access_license = settings.NAVER_AD_ACCESS_LICENSE
        self.secret_key = settings.NAVER_AD_SECRET_KEY

    def _generate_signature(self, timestamp, method, path):
        message = f"{timestamp}.{method}.{path}"
        hash = hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(hash).decode('utf-8')

    def _get_headers(self, method, path):
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path)
        return {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Timestamp": timestamp,
            "X-API-KEY": self.access_license,
            "X-Customer": self.customer_id,
            "X-Signature": signature
        }

    def sync_campaigns(self, client_id: str):
        """네이버 캠페인 정보를 가져와 DB에 동기화합니다."""
        path = "/ncc/campaigns"
        headers = self._get_headers("GET", path)
        
        response = requests.get(self.base_url + path, headers=headers)
        if response.status_code != 200:
            logger.error(f"Naver API Error (Sync Campaigns): {response.status_code}")
            return False

        naver_campaigns = response.json()
        
        # 1. 플랫폼 연결 확인 또는 생성
        connection = self.db.query(PlatformConnection).filter(
            PlatformConnection.client_id == client_id,
            PlatformConnection.platform == PlatformType.NAVER_AD
        ).first()
        
        if not connection:
            connection = PlatformConnection(
                client_id=client_id,
                platform=PlatformType.NAVER_AD,
                account_id=self.customer_id,
                status="ACTIVE"
            )
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)

        # 2. 캠페인 동기화
        for nc in naver_campaigns:
            campaign = self.db.query(Campaign).filter(
                Campaign.connection_id == connection.id,
                Campaign.external_id == nc['nccCampaignId']
            ).first()
            
            if not campaign:
                campaign = Campaign(
                    connection_id=connection.id,
                    external_id=nc['nccCampaignId'],
                    name=nc['name'],
                    status=nc['userLock'] == 'N' and 'ACTIVE' or 'PAUSED'
                )
                self.db.add(campaign)
            else:
                campaign.name = nc['name']
                campaign.status = nc['userLock'] == 'N' and 'ACTIVE' or 'PAUSED'
        
        self.db.commit()
        return True

    def sync_daily_metrics(self, campaign_external_id: str, date: datetime):
        """특정 날짜의 캠페인 성과 데이터를 수집합니다."""
        # Note: 네이버 통계 API (/stats)는 별도의 비동기 요청이나 대량 조회가 필요할 수 있음
        # 여기서는 단순화된 조회를 가정하거나 샘플 구현
        # 실제 운영 시에는 Stat Report API를 사용하여 배치 처리하는 것이 안정적임
        pass
