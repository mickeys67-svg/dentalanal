from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import DailyRank, Target, Keyword, TargetType, PlatformType
from app.schemas.scraping import PlaceResultItem, ViewResultItem
from typing import List, Union
from uuid import uuid4

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_keyword(self, term: str) -> Keyword:
        keyword = self.db.query(Keyword).filter(Keyword.term == term).first()
        if not keyword:
            keyword = Keyword(id=uuid4(), term=term)
            self.db.add(keyword)
            self.db.commit()
            self.db.refresh(keyword)
        return keyword

    def get_or_create_target(self, name: str, url: str = None) -> Target:
        target = self.db.query(Target).filter(Target.name == name).first()
        if not target:
            # Default to OTHERS if not pre-defined
            # In a real app, logic might be more complex to identify OWNER/COMPETITOR
            target = Target(id=uuid4(), name=name, type=TargetType.OTHERS, urls={"default": url} if url else None)
            self.db.add(target)
            self.db.commit()
            self.db.refresh(target)
        return target

    def save_place_results(self, keyword_str: str, results: List[dict]):
        keyword = self.get_or_create_keyword(keyword_str)
        
        for item in results:
            target_name = item.get("name")
            if not target_name: continue
            
            target = self.get_or_create_target(target_name)
            
            rank = DailyRank(
                id=uuid4(),
                target_id=target.id,
                keyword_id=keyword.id,
                platform=PlatformType.NAVER_PLACE,
                rank=item.get("rank"),
            )
            self.db.add(rank)
        
        self.db.commit()

    def save_view_results(self, keyword_str: str, results: List[dict]):
        keyword = self.get_or_create_keyword(keyword_str)
        
        for item in results:
            # For Blog, target name is blog_name
            target_name = item.get("blog_name")
            if not target_name: continue
             
            title = item.get("title")
            link = item.get("link")

            target = self.get_or_create_target(target_name, url=link)
            
            rank = DailyRank(
                id=uuid4(),
                target_id=target.id,
                keyword_id=keyword.id,
                platform=PlatformType.NAVER_VIEW,
                rank=item.get("rank"),
            )
            self.db.add(rank)
        
        self.db.commit()

    def calculate_sov(self, keyword_str: str, target_name: str, platform: PlatformType, top_n: int = 5) -> dict:
        keyword = self.db.query(Keyword).filter(Keyword.term == keyword_str).first()
        if not keyword:
            return {"sov": 0.0, "total": 0, "hits": 0, "keyword": keyword_str}

        # Filter by Rank <= top_n
        
        # Total possible slots is usually top_n? 
        # Or is SOV = (My Appearances in Top N) / (Total Top N Slots)?
        # For a single keyword, there are exactly 'top_n' slots in a theoretical sense, 
        # but realistically we just check how many times 'target' appears in the top_n results we scraped.
        # If we assume SOV means "Share of Voice in Top N", it is usually:
        # (Count of Target in Top N) / (Total Slots in Top N, which is top_n) * 100 ?
        # OR (Count of Target in Top N) / (Total Items Scraped in Top N) * 100 ?
        
        # Let's count how many items we actually have in top_n for this keyword (denominator)
        # In a perfect world, this is 'top_n'. But maybe we only scraped 3 items.
        
        total_in_range_count = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform,
            DailyRank.rank <= top_n
        ).count()
        
        # Denominator choice:
        # Option A: top_n (Fixed slots) -> If we scraped less, SOV might be lower than expected?
        # Option B: total_in_range_count -> Share among *captured* top N.
        # User asked for "Exposure frequency within 1-5 rank".
        # Let's use 'top_n' as the simpler denominator for "Share of Voice", 
        # implying "What portion of the Top N real estate do I own?"
        
        # However, if naive scraping returned 0 items, SOV is 0.
        denominator = top_n 
        
        if denominator == 0:
             return {"sov": 0.0, "total": 0, "hits": 0, "keyword": keyword_str}

        # Count hits for target in top_n
        target = self.db.query(Target).filter(Target.name == target_name).first()
        hits = 0
        if target:
            hits = self.db.query(DailyRank).filter(
                DailyRank.keyword_id == keyword.id,
                DailyRank.platform == platform,
                DailyRank.target_id == target.id,
                DailyRank.rank <= top_n
            ).count()

    def get_daily_ranks(self, keyword_str: str, platform: PlatformType) -> List[dict]:
        keyword = self.db.query(Keyword).filter(Keyword.term == keyword_str).first()
        if not keyword:
            return []
            
        # Get latest distinct ranks? Or just all for today?
        # For simplicity, latest 100 for this keyword/platform
        ranks = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform
        ).order_by(DailyRank.captured_at.desc(), DailyRank.rank.asc()).limit(100).all()
        
        # We need to filter by latest captured_at batch.
        if not ranks:
            return []
            
        latest_time = ranks[0].captured_at
        # Filter only those with same time (approx)
        current_batch = [r for r in ranks if abs((r.captured_at - latest_time).total_seconds()) < 60]
        
        results = []
        for r in current_batch:
            title = r.target.name
            url = r.target.urls.get("default") if r.target.urls else None
            
            results.append({
                "rank": r.rank,
                "title": title,
                "blog_name": r.target.name if platform == PlatformType.NAVER_VIEW else None, # Simplified
                "link": url,
                "created_at": r.captured_at
            })
            
        return sorted(results, key=lambda x: x['rank'])

    def get_competitor_analysis(self, keyword_str: str, platform: PlatformType, top_n: int = 10) -> dict:
        keyword = self.db.query(Keyword).filter(Keyword.term == keyword_str).first()
        if not keyword:
            return {"keyword": keyword_str, "platform": platform.value, "top_n": top_n, "competitors": []}
            
        # Get latest ranks to identify current competitors
        ranks = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform,
            DailyRank.rank <= top_n
        ).order_by(DailyRank.captured_at.desc(), DailyRank.rank.asc()).limit(100).all()

        if not ranks:
            return {"keyword": keyword_str, "platform": platform.value, "top_n": top_n, "competitors": []}

        latest_time = ranks[0].captured_at
        current_batch = [r for r in ranks if abs((r.captured_at - latest_time).total_seconds()) < 60]
        
        # Aggregate by Target
        stats = {} # target_id -> {name, count, total_rank}
        for r in current_batch:
            tid = r.target_id
            if tid not in stats:
                stats[tid] = {"name": r.target.name, "count": 0, "total_rank": 0}
            stats[tid]["count"] += 1
            stats[tid]["total_rank"] += r.rank
            
        total_slots = len(current_batch)
        competitors = []
        for tid, s in stats.items():
            competitors.append({
                "name": s["name"],
                "rank_count": s["count"],
                "avg_rank": s["total_rank"] / s["count"],
                "share": (s["count"] / total_slots) * 100 if total_slots > 0 else 0
            })
            
        # Sort by rank_count desc, then avg_rank asc
        competitors.sort(key=lambda x: (-x["rank_count"], x["avg_rank"]))
        
        return {
            "keyword": keyword_str,
            "platform": platform.value,
            "top_n": top_n,
            "competitors": competitors
        }

