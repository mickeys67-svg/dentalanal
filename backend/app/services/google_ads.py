import os
from typing import List, Dict

# ⚠️ 가짜 데이터 금지:
#   이전 버전은 developer_token 이 없거나 customer_id == "stub" 이면 하드코딩된
#   목업 캠페인과 매 호출마다 random.randint() 로 지어낸 클릭/노출/비용/전환을
#   반환했다(사기). 실제 Google Ads 성과는 사용자의 Google Ads 계정 +
#   developer token/OAuth 없이는 조회할 수 없다. 진짜 출처가 없으므로 가짜 수치를
#   만들지 않고, 미연동 상태에서는 빈 결과를 반환한다.


class GoogleAdsService:
    def __init__(self, developer_token: str = None, client_id: str = None, client_secret: str = None):
        self.developer_token = developer_token or os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")
        self.client_id = client_id or os.getenv("GOOGLE_ADS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_ADS_CLIENT_SECRET")

    def is_connected(self) -> bool:
        return bool(self.developer_token and self.client_id and self.client_secret)

    def get_campaigns(self, customer_id: str) -> List[Dict]:
        """
        Google Ads API 로 캠페인 조회. 자격증명 미설정 시 빈 목록(가짜 없음).
        실제 연동은 google-ads 클라이언트 구현 필요.
        """
        if not self.is_connected():
            return []
        # TODO: 실제 Google Ads API 연동
        return []

    def get_daily_metrics(self, customer_id: str, date: str) -> List[Dict]:
        """
        일별 성과 조회. 자격증명 미설정 시 빈 목록(가짜 수치 생성 안 함).
        """
        if not self.is_connected():
            return []
        # TODO: 실제 Google Ads API 연동
        return []
