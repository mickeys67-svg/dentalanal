from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import DailyRank, Target, Keyword, TargetType, PlatformType
from typing import List, Optional
import datetime

class CompetitorService:
    def __init__(self, db: Session):
        self.db = db

    def get_competitor_landscape(self, keyword_str: str, platform: PlatformType, top_n: int = 10) -> dict:
        """
        Analyzes the top N competitors for a specific keyword and platform.
        Refines AnalysisService logic with more dental-specific insights.
        """
        keyword = self.db.query(Keyword).filter(Keyword.term == keyword_str).first()
        if not keyword:
            return {"keyword": keyword_str, "status": "NOT_FOUND", "competitors": []}

        # Get the most recent capture time for this keyword
        latest_rank = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform
        ).order_by(DailyRank.captured_at.desc()).first()

        if not latest_rank:
            return {"keyword": keyword_str, "status": "NO_DATA", "competitors": []}

        ranks = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform,
            DailyRank.captured_at == latest_rank.captured_at,
            DailyRank.rank <= top_n
        ).order_by(DailyRank.rank.asc()).all()

        competitors = []
        for r in ranks:
            competitors.append({
                "rank": r.rank,
                "name": r.target.name,
                "type": r.target.type.value if hasattr(r.target.type, 'value') else "OTHERS",
                "is_threat": r.target.type == TargetType.COMPETITOR,
                "url": r.target.urls.get("default") if r.target.urls else None
            })

        return {
            "keyword": keyword_str,
            "platform": platform.value,
            "captured_at": latest_rank.captured_at,
            "top_n": top_n,
            "total_slots": len(ranks),
            "competitors": competitors
        }

    async def estimate_ad_spend(self, keywords: List[str]) -> List[dict]:
        """
        키워드별 실측 월간검색수 · 월평균 클릭수 · 경쟁정도.
        출처: 네이버 검색광고 키워드도구 API (direct-real, 실측값).

        ⚠️ 가짜 데이터 금지:
          - 이전엔 모든 키워드에 cpc=1500 / volume=2000 고정 상수를 넣고 광고비를
            지어냈다(사기). 이를 실측 볼륨으로 교체.
          - 키워드도구는 CPC(원)를 제공하지 않는다. CPC 실데이터 소스가 없으므로
            '월 광고비(원)' 추정치는 산출하지 않는다(없는 값을 지어내지 않음).
            실측 가능한 볼륨/클릭수/경쟁도만 반환한다.
        """
        from app.external_apis.naver_keyword_tool import NaverKeywordToolClient

        client = NaverKeywordToolClient()
        if not client.is_configured():
            return [
                {"keyword": kw, "no_data": True,
                 "reason": "네이버 검색광고 자격증명(NAVER_AD_*) 미설정"}
                for kw in keywords
            ]
        try:
            data = await client.get_keyword_stats(keywords, related_limit=0)
        except Exception as e:
            return [
                {"keyword": kw, "no_data": True, "reason": f"네이버 조회 실패: {e}"}
                for kw in keywords
            ]

        results = []
        for s in data.get("keywords", []):
            results.append({
                "keyword": s.get("input_keyword"),
                "monthly_volume": s.get("monthly_total"),      # 실측
                "monthly_masked": s.get("monthly_masked", False),  # "< 10" 마스킹 여부
                "avg_monthly_clicks_pc": s.get("monthly_avg_pc_clicks"),
                "avg_monthly_clicks_mobile": s.get("monthly_avg_mobile_clicks"),
                "competition": s.get("comp_idx"),              # 높음/중간/낮음 (실측)
                "no_data": s.get("no_data", False),
                "source": "NAVER_SEARCHAD_KEYWORDTOOL",
                "note": "광고비(원) 추정은 CPC 실데이터 소스 부재로 미제공",
            })
        return results

    def get_reputation_comparison(self, hospital_names: List[str]) -> List[dict]:
        """
        경쟁사 평판(별점/리뷰수) 비교.

        ⚠️ 가짜 데이터 금지:
          별점/리뷰수의 실데이터 소스(Google Business Profile / Kakao Map API 등)가
          연동되어 있지 않다. 이전엔 이름 기반 의사난수로 4.0~5.0 별점을 지어냈다(사기).
          진짜 출처가 없으므로 평판 수치는 만들지 않고 미연동으로 정직 표기하며,
          DB에 저장된 실제 사실(추적 대상 여부/자사 여부)만 반환한다.
        """
        results = []
        for name in hospital_names:
            target = self.db.query(Target).filter(Target.name == name).first()
            results.append({
                "hospital": name,
                "rating": None,
                "review_count": None,
                "monthly_increase": None,
                "reputation_available": False,
                "reason": "평판 API(구글 비즈니스/카카오맵) 미연동",
                "is_owner": target.type == TargetType.OWNER if target else False,
                "tracked": target is not None,
            })
        return results
