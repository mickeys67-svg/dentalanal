import time
import hashlib
import hmac
import base64
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import PlatformConnection, Campaign, MetricsDaily, PlatformType, AdGroup, AdKeyword, AdMetricsDaily
import logging
import uuid

logger = logging.getLogger(__name__)

class NaverAdsService:
    def __init__(self, db: Session, credentials: dict = None):
        self.db = db
        self.base_url = "https://api.searchad.naver.com"
        
        # [FIX] env vars (GitHub Secrets) 항상 최우선.
        # DB credentials는 env var가 없을 때만 폴백으로 사용.
        # "demo_key", "your_key" 등 placeholder 값은 무시.
        _PLACEHOLDER = {'demo_key', 'your_key', 'test_key', 'placeholder', 'none', '', None}

        creds = credentials or {}

        def _valid(v):
            return v if v and v.strip().lower() not in _PLACEHOLDER else None

        db_customer_id    = _valid(creds.get('customer_id'))
        db_access_license = _valid(creds.get('api_key') or creds.get('access_license'))
        db_secret_key     = _valid(creds.get('secret_key'))

        self.customer_id    = settings.NAVER_AD_CUSTOMER_ID  or db_customer_id
        self.access_license = settings.NAVER_AD_ACCESS_LICENSE or db_access_license
        self.secret_key     = settings.NAVER_AD_SECRET_KEY    or db_secret_key

        logger.info(
            f"[NaverAds] Init — customer_id={'set' if self.customer_id else 'MISSING'} "
            f"license={'set' if self.access_license else 'MISSING'} "
            f"secret={'set' if self.secret_key else 'MISSING'}"
        )

        # Setup Retry Strategy
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

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
        
        try:
            response = self.session.get(self.base_url + path, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Naver API Error (Sync Campaigns): {response.status_code} - {response.text}")
                return False
        except requests.exceptions.Timeout:
            logger.error("Naver API Timeout during sync_campaigns")
            return False
        except Exception as e:
            logger.error(f"Naver API Connection Error: {e}")
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
                status="ACTIVE",
                credentials={
                    "customer_id": self.customer_id,
                    "access_license": self.access_license,
                    "secret_key": self.secret_key
                }
            )
            self.db.add(connection)
            self.db.commit()
            self.db.refresh(connection)
        else:
            # Update credentials if they changed in .env/secrets
            connection.credentials = {
                "customer_id": self.customer_id,
                "access_license": self.access_license,
                "secret_key": self.secret_key
            }
            connection.account_id = self.customer_id
            self.db.add(connection)
            self.db.commit()

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

    def sync_ad_groups(self, campaign_external_id: str):
        """캠페인 하위의 광고그룹(AdGroup)을 동기화합니다."""
        path = "/ncc/adgroups"
        params = {"nccCampaignId": campaign_external_id}
        headers = self._get_headers("GET", path)

        try:
            response = self.session.get(self.base_url + path, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Naver API AdGroup Error: {response.status_code} - {response.text}")
                return []
            
            ad_groups_data = response.json()
            
            # DB Campaign ID Lookup
            campaign = self.db.query(Campaign).filter(Campaign.external_id == campaign_external_id).first()
            if not campaign:
                logger.error(f"Campaign not found for external_id: {campaign_external_id}")
                return []

            synced_groups = []
            for group_data in ad_groups_data:
                ad_group = self.db.query(AdGroup).filter(AdGroup.external_id == group_data["nccAdgroupId"]).first()
                if not ad_group:
                    ad_group = AdGroup(
                        id=uuid.uuid4(),
                        campaign_id=campaign.id,
                        external_id=group_data["nccAdgroupId"],
                        name=group_data["name"],
                        status=group_data["userLock"] == "N" and "ACTIVE" or "PAUSED"
                    )
                    self.db.add(ad_group)
                else:
                    ad_group.name = group_data["name"]
                    ad_group.status = group_data["userLock"] == "N" and "ACTIVE" or "PAUSED"
                
                synced_groups.append(ad_group)
            
            self.db.commit()
            return synced_groups

        except Exception as e:
            logger.error(f"Failed to sync ad groups: {e}")
            return []

    def sync_keywords(self, ad_group_external_id: str):
        """광고그룹 하위의 키워드(AdKeyword)를 동기화합니다."""
        path = "/ncc/keywords"
        params = {"nccAdgroupId": ad_group_external_id}
        headers = self._get_headers("GET", path)

        try:
            response = self.session.get(self.base_url + path, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Naver API Keyword Error: {response.status_code} - {response.text}")
                return []

            keywords_data = response.json()

            # DB AdGroup Lookup
            ad_group = self.db.query(AdGroup).filter(AdGroup.external_id == ad_group_external_id).first()
            if not ad_group:
                return []

            synced_keywords = []
            for kw_data in keywords_data:
                keyword = self.db.query(AdKeyword).filter(AdKeyword.external_id == kw_data["nccKeywordId"]).first()
                if not keyword:
                    keyword = AdKeyword(
                        id=uuid.uuid4(),
                        ad_group_id=ad_group.id,
                        external_id=kw_data["nccKeywordId"],
                        text=kw_data["keyword"],
                        bid_amt=kw_data.get("bidAmt", 0),
                        status=kw_data["userLock"] == "N" and "ACTIVE" or "PAUSED"
                    )
                    self.db.add(keyword)
                else:
                    keyword.bid_amt = kw_data.get("bidAmt", 0)
                    keyword.status = kw_data["userLock"] == "N" and "ACTIVE" or "PAUSED"
                
                synced_keywords.append(keyword)

            self.db.commit()
            return synced_keywords

        except Exception as e:
            logger.error(f"Failed to sync keywords: {e}")
            return []

    def sync_daily_metrics(self, external_id: str, date_str: str, entity_type: str = "campaign"):
        """
        특정 엔티티(캠페인, 광고그룹, 키워드)의 성과 데이터를 수집합니다.
        entity_type: 'campaign', 'adgroup', 'keyword' (DB저장용 구분, API호출은 ID로 자동처리됨)
        """
        # Naver Ads Stats API: GET /stats
        time_range = {"from": date_str, "to": date_str}
        params = {
            "ids": external_id,
            "fields": "impCnt,clickCnt,salesAmt,convCnt,ctr,cpc,avgRnk", # Added CTR, CPC for validation
            "timeRange": json.dumps(time_range)
        }
        
        path = "/stats"
        headers = self._get_headers("GET", path)
        try:
            response = self.session.get(self.base_url + path, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"Naver API Stats Error ({entity_type}:{external_id}): {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            if not data or 'data' not in data or not data['data']:
                # logger.debug(f"No API stats data found for {external_id} on {date_str}")
                return None
            
            # Extract first record
            stats = data['data'][0]
            return {
                "spend": float(stats.get("salesAmt", 0)),
                "impressions": int(stats.get("impCnt", 0)),
                "clicks": int(stats.get("clickCnt", 0)),
                "conversions": int(stats.get("convCnt", 0)),
                "ctr": float(stats.get("ctr", 0)),
                "cpc": float(stats.get("cpc", 0))
            }
        except requests.exceptions.Timeout:
            logger.error(f"Naver API Timeout for stats: {external_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch real Naver API metrics: {e}")
            return None

    def sync_all_campaign_metrics(self, connection_id: uuid.UUID, date_str: str):
        """
        커넥션에 연결된 모든 캠페인 -> 광고그룹 -> 키워드를 순회하며 데이터를 수집합니다.
        (Granular Sync: Campaign > AdGroup > Keyword)
        """
        campaigns = self.db.query(Campaign).filter(Campaign.connection_id == connection_id).all()
        results_count = 0
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        for cp in campaigns:
            if not cp.external_id:
                continue
            
            # 1. Sync Campaign Metrics (Legacy/Summary)
            camp_data = self.sync_daily_metrics(cp.external_id, date_str, "campaign")
            if camp_data:
                metrics = self.db.query(MetricsDaily).filter(
                    MetricsDaily.campaign_id == cp.id,
                    MetricsDaily.date == target_date,
                    MetricsDaily.source == 'API'
                ).first()
                if not metrics:
                    metrics = MetricsDaily(id=uuid.uuid4(), campaign_id=cp.id, date=target_date, source='API')
                    self.db.add(metrics)
                
                metrics.spend = camp_data["spend"]
                metrics.impressions = camp_data["impressions"]
                metrics.clicks = camp_data["clicks"]
                metrics.conversions = camp_data["conversions"]

            # 2. Sync AdGroups
            ad_groups = self.sync_ad_groups(cp.external_id)
            for ag in ad_groups:
                # 3. Sync Keywords
                keywords = self.sync_keywords(ag.external_id)
                
                # 4. Sync Metrics for Keywords
                for kw in keywords:
                    kw_data = self.sync_daily_metrics(kw.external_id, date_str, "keyword")
                    if kw_data:
                        ad_metrics = self.db.query(AdMetricsDaily).filter(
                            AdMetricsDaily.keyword_id == kw.id,
                            AdMetricsDaily.date == target_date
                        ).first()
                        
                        if not ad_metrics:
                            ad_metrics = AdMetricsDaily(
                                id=uuid.uuid4(), 
                                date=target_date, 
                                ad_group_id=ag.id, 
                                keyword_id=kw.id
                            )
                            self.db.add(ad_metrics)
                        
                        ad_metrics.impressions = kw_data["impressions"]
                        ad_metrics.clicks = kw_data["clicks"]
                        ad_metrics.spend = kw_data["spend"]
                        ad_metrics.conversions = kw_data["conversions"]
                        ad_metrics.ctr = kw_data["ctr"]
                        ad_metrics.cpc = kw_data["cpc"]
                        results_count += 1
                        
            # Intermediate commit per campaign to save progress
            self.db.commit()
        
        return results_count

    def validate_api(self) -> dict:
        """현재 설정된 키가 실제로 작동하는지 네이버 서버에 직접 물어봅니다."""
        path = "/ncc/campaigns"
        # 1개만 조회하여 최소한의 리소스로 인증 성공 여부 확인
        headers = self._get_headers("GET", path)
        try:
            response = self.session.get(self.base_url + path, headers=headers, params={"size": 1})
            if response.status_code == 200:
                return {"status": "HEALTHY", "message": "성공적으로 연결되었습니다."}
            elif response.status_code == 401:
                return {"status": "UNAUTHORIZED", "message": "API 키 또는 시크릿이 올바르지 않습니다."}
            else:
                return {"status": "ERROR", "message": f"오류 발생 ({response.status_code}): {response.text}"}
        except Exception as e:
            return {"status": "CATASTROPHIC", "message": f"통신 불가: {str(e)}"}
