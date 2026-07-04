import os
from typing import List, Dict

# ⚠️ 가짜 데이터 금지:
#   이전 버전은 META_ADS_ACCESS_TOKEN 이 없으면 하드코딩된 목업 캠페인과
#   매 호출마다 random.randint() 로 지어낸 클릭/노출/비용/전환을 반환했다(사기).
#   실제 Meta(Facebook/Instagram) 광고 성과는 사용자의 Meta 광고 계정 +
#   Graph API access token 없이는 조회할 수 없다. 진짜 출처가 없으므로
#   가짜 수치를 만들지 않고, 미연동 상태에서는 빈 결과를 반환한다.


class MetaAdsService:
    def __init__(self, access_token: str = None, ad_account_id: str = None):
        self.access_token = access_token or os.getenv("META_ADS_ACCESS_TOKEN")
        self.ad_account_id = ad_account_id or os.getenv("META_AD_ACCOUNT_ID")

    def is_connected(self) -> bool:
        return bool(self.access_token and self.ad_account_id)

    def get_campaigns(self) -> List[Dict]:
        """
        Meta Graph API 로 캠페인 조회. 자격증명 미설정 시 빈 목록(가짜 없음).
        실제 연동은 Graph API 구현 필요.
        """
        if not self.is_connected():
            return []
        # TODO: 실제 Graph API 연동
        return []

    def get_daily_metrics(self, date: str) -> List[Dict]:
        """
        일별 성과 조회. 자격증명 미설정 시 빈 목록(가짜 수치 생성 안 함).
        """
        if not self.is_connected():
            return []
        # TODO: 실제 Graph API 연동
        return []
