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

    def estimate_ad_spend(self, keywords: List[str]) -> List[dict]:
        """
        Estimates monthly ad spend for dental keywords.
        In a real app, this would fetch from Naver Search Ads API / Google Ads API.
        Mocking with dental industry averages for now.
        """
        results = []
        for kw in keywords:
            # Dental Industry Mock Data
            if "임플란트" in kw:
                cpc = 5200
                volume = 8500
            elif "교정" in kw:
                cpc = 3800
                volume = 6200
            elif "치과" in kw:
                cpc = 3200
                volume = 12000
            else:
                cpc = 1500
                volume = 2000
            
            monthly_est = (cpc * volume * 0.05) # Assume 5% CTR for estimate
            results.append({
                "keyword": kw,
                "avg_cpc": cpc,
                "monthly_volume": volume,
                "est_min_spend": int(monthly_est * 0.7),
                "est_max_spend": int(monthly_est * 1.3)
            })
        return results

    def get_reputation_comparison(self, hospital_names: List[str]) -> List[dict]:
        """
        Compares reputation (Ratings & Reviews) across competitors.
        """
        # In a real app, this would query Google Business Profile / Kakao Map APIs.
        # Here we mock the comparison based on targets stored in DB.
        results = []
        for name in hospital_names:
            target = self.db.query(Target).filter(Target.name == name).first()
            
            # Using stable pseudo-random data for demonstration consistency
            seed = sum(ord(c) for c in name)
            import random
            random.seed(seed)
            
            rating = round(random.uniform(4.0, 5.0), 1)
            reviews = random.randint(50, 500)
            monthly_inc = random.randint(2, 25)
            
            results.append({
                "hospital": name,
                "rating": rating,
                "review_count": reviews,
                "monthly_increase": monthly_inc,
                "is_owner": target.type == TargetType.OWNER if target else False
            })
        return sorted(results, key=lambda x: x["rating"], reverse=True)
