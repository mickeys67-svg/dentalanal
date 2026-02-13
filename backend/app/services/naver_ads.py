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
import uuid

logger = logging.getLogger(__name__)

class NaverAdsService:
    def __init__(self, db: Session, credentials: dict = None):
        self.db = db
        self.base_url = "https://api.searchad.naver.com"
        
        # 기본값은 settings에서 가져오되, 전달된 credentials가 있으면 우선함
        creds = credentials or {}
        self.customer_id = creds.get('customer_id') or settings.NAVER_AD_CUSTOMER_ID
        self.access_license = creds.get('api_key') or creds.get('access_license') or settings.NAVER_AD_ACCESS_LICENSE
        self.secret_key = creds.get('secret_key') or settings.NAVER_AD_SECRET_KEY

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
            logger.error(f"Naver API Error (Sync Campaigns): {response.status_code} - {response.text}")
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
            # 2a. external_id로 먼저 확인 (공식 API 기준)
            campaign = self.db.query(Campaign).filter(
                Campaign.connection_id == connection.id,
                Campaign.external_id == nc['nccCampaignId']
            ).first()
            
            # 2b. 이름으로 재확인 (스크래퍼가 먼저 생성했을 경우 ID 매칭 보정)
            if not campaign:
                campaign = self.db.query(Campaign).filter(
                    Campaign.connection_id == connection.id,
                    Campaign.name == nc['name']
                ).first()
                if campaign:
                    logger.info(f"Existing campaign found by name: {nc['name']}. Mapping external_id to {nc['nccCampaignId']}")
                    campaign.external_id = nc['nccCampaignId']
            
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

    def sync_daily_metrics(self, campaign_external_id: str, date_str: str):
        """특정 날짜의 캠페인 성과 데이터를 수집하여 source='API'로 저장합니다."""
        # Naver Ads Stats API: GET /stats
        # fields: impCnt(노출), clickCnt(클릭), salesAmt(비용), convCnt(전환)
        time_range = {"from": date_str, "to": date_str}
        params = {
            "ids": campaign_external_id,
            "fields": "impCnt,clickCnt,salesAmt,convCnt",
            "timeRange": json.dumps(time_range)
        }
        
        path = "/stats"
        headers = self._get_headers("GET", path)
        try:
            response = requests.get(self.base_url + path, headers=headers, params=params)
            if response.status_code != 200:
                logger.error(f"Naver API Stats Error: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            if not data or 'data' not in data or not data['data']:
                logger.warning(f"No API stats data found for {campaign_external_id} on {date_str}")
                return None
            
            # Extract first record
            stats = data['data'][0]
            return {
                "spend": float(stats.get("salesAmt", 0)),
                "impressions": int(stats.get("impCnt", 0)),
                "clicks": int(stats.get("clickCnt", 0)),
                "conversions": int(stats.get("convCnt", 0))
            }
        except Exception as e:
            logger.error(f"Failed to fetch real Naver API metrics: {e}")
            return None

    def sync_all_campaign_metrics(self, connection_id: uuid.UUID, date_str: str):
        """커넥션에 연결된 모든 캠페인의 API 지표를 수집합니다."""
        campaigns = self.db.query(Campaign).filter(Campaign.connection_id == connection_id).all()
        results_count = 0
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        for cp in campaigns:
            if not cp.external_id:
                continue
                
            data = self.sync_daily_metrics(cp.external_id, date_str)
            if data:
                # Save as API source
                metrics = self.db.query(MetricsDaily).filter(
                    MetricsDaily.campaign_id == cp.id,
                    MetricsDaily.date == target_date,
                    MetricsDaily.source == 'API'
                ).first()
                
                if not metrics:
                    metrics = MetricsDaily(id=uuid.uuid4(), campaign_id=cp.id, date=target_date, source='API')
                    self.db.add(metrics)
                
                metrics.spend = data["spend"]
                metrics.impressions = data["impressions"]
                metrics.clicks = data["clicks"]
                metrics.conversions = data["conversions"]
                results_count += 1
        
        self.db.commit()
        return results_count
