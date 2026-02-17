from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import DailyRank, Target, Keyword, TargetType, PlatformType, MetricsDaily, Campaign, PlatformConnection, Lead, LeadActivity, LeadProfile, Report
from typing import List, Union, Optional, Any
from uuid import uuid4, UUID
import random
import datetime
import logging

class AnalysisService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        # [MIGRATE] Transitioned from MongoDB to Supabase (Option A)

    def _get_or_create_keyword(self, term: str, client_id: Optional[UUID] = None) -> Keyword:
        query = self.db.query(Keyword).filter(Keyword.term == term)
        if client_id:
            query = query.filter(Keyword.client_id == client_id)
        
        keyword = query.first()
        
        if not keyword:
            keyword = Keyword(id=uuid4(), term=term, client_id=client_id)
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

    def _save_raw_log_to_supabase(self, platform: PlatformType, keyword: str, data: Any):
        """Saves unstructured data to Supabase JSONB table (replacing MongoDB)."""
        try:
            from app.models.models import RawScrapingLog
            log_entry = RawScrapingLog(
                id=uuid4(),
                platform=platform,
                keyword=keyword,
                data=data
            )
            self.db.add(log_entry)
            self.db.flush() 
        except Exception as e:
            self.logger.error(f"Failed to save raw log to Supabase: {e}")

    def save_place_results(self, keyword_str: str, results: List[dict], client_id: Optional[UUID] = None):
        # Save Raw Data to Supabase (Option A Consolidation)
        self._save_raw_log_to_supabase(PlatformType.NAVER_PLACE, keyword_str, results)
        
        keyword = self._get_or_create_keyword(keyword_str, client_id)
        
        # Optimization: Pre-fetch all targets to avoid N+1
        target_names = [item.get("name") for item in results if item.get("name")]
        existing_targets = {t.name: t for t in self.db.query(Target).filter(Target.name.in_(target_names)).all()}
        
        for item in results:
            target_name = item.get("name")
            if not target_name: continue
            
            target = existing_targets.get(target_name)
            if not target:
                target = Target(id=uuid4(), name=target_name, type=TargetType.OTHERS)
                self.db.add(target)
                self.db.flush() # Ensure ID is available
                existing_targets[target_name] = target
            
            rank = DailyRank(
                id=uuid4(),
                client_id=client_id,
                target_id=target.id,
                keyword_id=keyword.id,
                platform=PlatformType.NAVER_PLACE,
                rank=item.get("rank"),
            )
            self.db.add(rank)
        self.db.commit()

    def save_view_results(self, keyword_str: str, results: List[dict], client_id: Optional[UUID] = None):
        # Save Raw Data to Supabase (Option A Consolidation)
        self._save_raw_log_to_supabase(PlatformType.NAVER_VIEW, keyword_str, results)
        
        keyword = self._get_or_create_keyword(keyword_str, client_id)
        
        target_names = [item.get("blog_name") for item in results if item.get("blog_name")]
        existing_targets = {t.name: t for t in self.db.query(Target).filter(Target.name.in_(target_names)).all()}
        
        for item in results:
            target_name = item.get("blog_name")
            if not target_name: continue
            
            target = existing_targets.get(target_name)
            if not target:
                target = Target(id=uuid4(), name=target_name, type=TargetType.OTHERS, urls={"default": item.get("link")} if item.get("link") else None)
                self.db.add(target)
                self.db.flush()
                existing_targets[target_name] = target
            
            rank = DailyRank(
                id=uuid4(),
                client_id=client_id,
                target_id=target.id,
                keyword_id=keyword.id,
                platform=PlatformType.NAVER_VIEW,
                rank=item.get("rank"),
            )
            self.db.add(rank)
        self.db.commit()

    def save_ad_results(self, keyword_str: str, results: List[dict], client_id: Optional[UUID] = None):
        # Save Raw Data to Supabase (Option A Consolidation)
        self._save_raw_log_to_supabase(PlatformType.NAVER_AD, keyword_str, results)
        
        keyword = self._get_or_create_keyword(keyword_str, client_id)
        
        target_names = [item.get("advertiser") for item in results if item.get("advertiser")]
        existing_targets = {t.name: t for t in self.db.query(Target).filter(Target.name.in_(target_names)).all()}
        
        for item in results:
            target_name = item.get("advertiser")
            if not target_name: continue
            
            target = existing_targets.get(target_name)
            if not target:
                target = Target(id=uuid4(), name=target_name, type=TargetType.OTHERS, urls={"default": item.get("display_url")} if item.get("display_url") else None)
                self.db.add(target)
                self.db.flush()
                existing_targets[target_name] = target
            
            rank = DailyRank(
                id=uuid4(),
                client_id=client_id,
                target_id=target.id,
                keyword_id=keyword.id,
                platform=PlatformType.NAVER_AD,
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
        top_rank = None
        
        if target:
            hits = self.db.query(DailyRank).filter(
                DailyRank.keyword_id == keyword.id,
                DailyRank.platform == platform,
                DailyRank.target_id == target.id,
                DailyRank.rank <= top_n
            ).count()
            
        # Find actual period for this keyword/platform ranks
        # For a single snapshot, we find the latest capture time
        latest_capture = self.db.query(func.max(DailyRank.captured_at)).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform
        ).scalar()
        
        period_str = latest_capture.strftime("%Y-%m-%d %H:%M") if latest_capture else None

        return {
            "sov": (hits / denominator) * 100 if denominator > 0 else 0,
            "total": denominator,
            "hits": hits,
            "keyword": keyword_str,
            "top_rank": top_rank,
            "period_start": period_str,
            "period_end": period_str
        }

    def get_daily_ranks(self, keyword_str: str, platform: PlatformType) -> List[dict]:
        from app.models.models import DailyRank, Keyword
        keyword = self.db.query(Keyword).filter(Keyword.term == keyword_str).first()
        if not keyword:
            return []
            
        # Get the latest ranks for this keyword/platform
        latest = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform
        ).order_by(DailyRank.captured_at.desc()).first()
        
        if not latest:
            return []
            
        ranks = self.db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.platform == platform,
            DailyRank.captured_at == latest.captured_at
        ).order_by(DailyRank.rank.asc()).all()
        
        return [{
            "rank": r.rank,
            "title": r.target.name,
            "link": r.target.urls.get("default") if r.target.urls else None,
            "created_at": r.captured_at
        } for r in ranks]

    def get_ranking_trend(self, keyword_str: str, target_name: str, platform: PlatformType, days: int = 30) -> List[dict]:
        keyword = self.db.query(Keyword).filter(Keyword.term == keyword_str).first()
        target = self.db.query(Target).filter(Target.name == target_name).first()
        
        if not keyword or not target:
            return []
            
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # Get ranks for the target in the last N days
        ranks = self.db.query(
            func.date(DailyRank.captured_at).label("date"),
            func.min(DailyRank.rank).label("min_rank")
        ).filter(
            DailyRank.keyword_id == keyword.id,
            DailyRank.target_id == target.id,
            DailyRank.platform == platform,
            DailyRank.captured_at >= start_date
        ).group_by(func.date(DailyRank.captured_at)).order_by("date").all()
        
        return [{"date": str(r.date), "rank": r.min_rank} for r in ranks]

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
        
        period_str = latest_time.strftime("%Y-%m-%d %H:%M") if latest_time else None

        return {
            "keyword": keyword_str,
            "platform": platform.value,
            "top_n": top_n,
            "competitors": competitors,
            "period_start": period_str,
            "period_end": period_str
        }

    def get_weekly_sov_summary(self, target_name: str, keywords: List[str], platform: PlatformType) -> dict:
        """
        Aggregate SOV across multiple keywords for the last 7 days.
        """
        import datetime
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=7)
        
        target = self.db.query(Target).filter(Target.name == target_name).first()
        if not target:
            return {"target": target_name, "avg_sov": 0.0, "keyword_details": []}
            
        details = []
        total_sov = 0.0
        
        for k_str in keywords:
            data = self.calculate_sov(k_str, target_name, platform, top_n=5)
            details.append(data)
            total_sov += data["sov"]
            
        avg_sov = total_sov / len(keywords) if keywords else 0
        
        period_start_str = start_date.strftime("%Y-%m-%d")
        period_end_str = end_date.strftime("%Y-%m-%d")

        return {
            "target": target_name,
            "avg_sov": avg_sov,
            "period_start": period_start_str,
            "period_end": period_end_str,
            "period": f"{period_start_str} ~ {period_end_str}",
            "keyword_details": details
        }

    def get_funnel_data(self, client_id: str, start_date: datetime.date = None, end_date: datetime.date = None, days: int = 30) -> dict:
        """
        Calculate funnel stages: Impressions -> Clicks -> Conversions with rates.
        """
        from app.models.models import MetricsDaily, Campaign, PlatformConnection
        
        # Determine date range
        if not end_date:
            end_date = datetime.date.today()
        if not start_date:
            start_date = end_date - datetime.timedelta(days=days)
        
        # Determine best source (Fallback: RECONCILED > API > SCRAPER)
        source_filter = 'RECONCILED'
        recon_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'RECONCILED').limit(1).first()
        if not recon_exists:
            api_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'API').limit(1).first()
            source_filter = 'API' if api_exists else 'SCRAPER'
            self.logger.warning(f"No RECONCILED metrics found for funnel. Using {source_filter} fallback.")

        # Base query with filters
        query_base = self.db.query(MetricsDaily).join(Campaign).join(PlatformConnection).filter(
            PlatformConnection.client_id == client_id,
            MetricsDaily.date >= start_date,
            MetricsDaily.date <= end_date,
            MetricsDaily.source == source_filter
        )

        # Get actual period found in DB
        actual_period = self.db.query(
            func.min(MetricsDaily.date),
            func.max(MetricsDaily.date)
        ).select_from(query_base.subquery()).first()
        
        # Aggregate metrics
        results = self.db.query(
            func.sum(MetricsDaily.impressions).label("impressions"),
            func.sum(MetricsDaily.clicks).label("clicks"),
            func.sum(MetricsDaily.conversions).label("conversions")
        ).select_from(MetricsDaily)\
         .join(Campaign)\
         .join(PlatformConnection)\
         .filter(
            PlatformConnection.client_id == client_id,
            MetricsDaily.date >= start_date,
            MetricsDaily.date <= end_date,
            MetricsDaily.source == source_filter
        ).first()

        impressions = int(results.impressions or 0)
        clicks = int(results.clicks or 0)
        conversions = int(results.conversions or 0)
        
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cvr = (conversions / clicks * 100) if clicks > 0 else 0

        period_start_str = actual_period[0].strftime("%Y-%m-%d") if actual_period and actual_period[0] else None
        period_end_str = actual_period[1].strftime("%Y-%m-%d") if actual_period and actual_period[1] else None

        return {
            "items": [
                {"stage": "노출 (Impressions)", "value": impressions, "rate": None},
                {"stage": "클릭 (Clicks)", "value": clicks, "rate": round(ctr, 2), "unit": "% (CTR)"},
                {"stage": "전환 (Conversions)", "value": conversions, "rate": round(cvr, 2), "unit": "% (CVR)"}
            ],
            "period_start": period_start_str,
            "period_end": period_end_str,
            "period": f"{period_start_str} ~ {period_end_str}" if period_start_str else "측정 기간 데이터 없음"
        }

    def get_cohort_data(self, client_id: str) -> List[dict]:
        """Calculates real cohort retention data using Leads and LeadActivities tables."""
        cohorts = self.db.query(
            Lead.cohort_month,
            func.count(Lead.id).label("size")
        ).filter(Lead.client_id == client_id)\
         .group_by(Lead.cohort_month)\
         .order_by(Lead.cohort_month.asc()).all()
        
        if not cohorts:
            return []
            
        results = []
        for c in cohorts:
            activities = self.db.query(
                LeadActivity.activity_month,
                func.count(func.distinct(LeadActivity.lead_id)).label("active_count")
            ).join(Lead).filter(
                Lead.client_id == client_id,
                Lead.cohort_month == c.cohort_month
            ).group_by(LeadActivity.activity_month).all()
            
            c_y, c_m = map(int, c.cohort_month.split('-'))
            retention = [100.0]
            for act in sorted(activities, key=lambda x: x.activity_month):
                a_y, a_m = map(int, act.activity_month.split('-'))
                offset = (a_y * 12 + a_m) - (c_y * 12 + c_m)
                if offset > 0:
                    rate = (act.active_count / c.size * 100) if c.size > 0 else 0
                    retention.append(round(rate, 1))
            
            results.append({"month": c.cohort_month, "size": c.size, "retention": retention[:6]})
        return results

    def calculate_attribution(self, client_id: str) -> List[dict]:
        """
        [NEW] 기여도 분석 로직 구현.
        현재는 수집된 Lead 데이터의 소스별 분포를 반환합니다.
        """
        results = self.db.query(
            Lead.source.label("channel"),
            func.count(Lead.id).label("conversions"),
            func.sum(LeadProfile.total_revenue).label("revenue")
        ).join(LeadProfile, Lead.id == LeadProfile.lead_id)\
         .filter(Lead.client_id == client_id)\
         .group_by(Lead.source).all()
         
        if not results:
            # 기본 샘플 데이터 형식 반환 (통계 규격 맞춤)
            return [
                {"channel": "네이버 검색광고", "conversions": 0, "revenue": 0, "weight": 40},
                {"channel": "네이버 플레이스", "conversions": 0, "revenue": 0, "weight": 35},
                {"channel": "블로그/리뷰", "conversions": 0, "revenue": 0, "weight": 25}
            ]
            
        total_conv = sum(r.conversions for r in results)
        return [{
            "channel": r.channel or "기타",
            "conversions": r.conversions,
            "revenue": float(r.revenue or 0),
            "weight": round((r.conversions / total_conv * 100), 1) if total_conv else 0
        } for r in results]

    def get_segment_analysis(self, client_id: str) -> List[dict]:
        """Aggregate performance by REAL audience segments."""
        region_stats = self.db.query(
            LeadProfile.region.label("label"),
            func.count(Lead.id).label("visitors"),
            func.sum(LeadProfile.total_conversions).label("conversions"),
            func.sum(LeadProfile.total_revenue).label("revenue")
        ).join(Lead).filter(Lead.client_id == client_id)\
         .group_by(LeadProfile.region).all()
         
        if not region_stats:
            return []
            
        return [{
            "segment": s.label or "기타",
            "visitors": int(s.visitors or 0),
            "conversion_rate": round((s.conversions / s.visitors * 100), 1) if s.visitors else 0,
            "roas": int(s.revenue / (s.visitors * 500) * 100) if s.visitors else 0
        } for s in region_stats]

    def generate_report_data(self, report_id: UUID):
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report: return
        
        try:
            report_data = {"widgets": []}
            for widget in report.template.config.get("widgets", []):
                widget_entry = {"id": widget["id"], "type": widget["type"], "data": self._generate_widget_data(widget, report)}
                report_data["widgets"].append(widget_entry)
            
            report.data, report.status = report_data, "COMPLETED"
            self.db.commit()
        except Exception as e:
            self.logger.error(f"Report Generation Error: {e}")
            report.status = "FAILED"
            self.db.commit()

    def _generate_widget_data(self, widget, report):
        w_type = widget.get("type")
        if w_type == "KPI_GROUP":
            metrics = self.db.query(
                func.sum(MetricsDaily.spend).label("spend"),
                func.sum(MetricsDaily.impressions).label("impressions"),
                func.sum(MetricsDaily.clicks).label("clicks"),
                func.sum(MetricsDaily.conversions).label("conversions")
            ).select_from(MetricsDaily).join(Campaign).join(PlatformConnection).filter(
                PlatformConnection.client_id == report.client_id,
                MetricsDaily.source == 'RECONCILED'
            ).first()
            return [
                {"label": "총 광고비", "value": int(metrics.spend or 0), "prefix": "₩"},
                {"label": "전환수", "value": int(metrics.conversions or 0)}
            ]
        elif w_type == "FUNNEL": return self.get_funnel_data(str(report.client_id))
        elif w_type == "COHORT": return self.get_cohort_data(str(report.client_id))
        elif w_type == "SOV": return self.get_weekly_sov_summary(report.client.name, widget.get("keywords", []), PlatformType.NAVER_PLACE)
        return None

    def get_efficiency_data(self, client_id: str, start_date: datetime.date = None, end_date: datetime.date = None, days: int = 30) -> dict:
        """
        Extract spend and conversion data per campaign/platform to analyze efficiency.
        """
        from app.models.models import MetricsDaily, Campaign, PlatformConnection
        
        # Determine date range
        if not end_date:
            end_date = datetime.date.today()
        if not start_date:
            start_date = end_date - datetime.timedelta(days=days)
        
        # Determine best source (Fallback: RECONCILED > API > SCRAPER)
        source_filter = 'RECONCILED'
        recon_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'RECONCILED').limit(1).first()
        if not recon_exists:
            api_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'API').limit(1).first()
            source_filter = 'API' if api_exists else 'SCRAPER'
            self.logger.warning(f"No RECONCILED metrics found for efficiency. Using {source_filter} fallback.")

        # Base query with filters
        query_base = self.db.query(MetricsDaily).join(Campaign, Campaign.id == MetricsDaily.campaign_id)\
         .join(PlatformConnection, PlatformConnection.id == Campaign.connection_id)\
         .filter(
             PlatformConnection.client_id == client_id,
             MetricsDaily.date >= start_date,
             MetricsDaily.date <= end_date,
             MetricsDaily.source == source_filter
         )

        # Get actual period found in DB
        actual_period = self.db.query(
            func.min(MetricsDaily.date),
            func.max(MetricsDaily.date)
        ).select_from(query_base.subquery()).first()

        # Get metrics aggregated by campaign
        results = query_base.with_entities(
            Campaign.name,
            PlatformConnection.platform,
            func.sum(MetricsDaily.spend).label("spend"),
            func.sum(MetricsDaily.clicks).label("clicks"),
            func.sum(MetricsDaily.conversions).label("conversions"),
            func.sum(MetricsDaily.impressions).label("impressions")
        ).group_by(Campaign.name, PlatformConnection.platform).all()

        items = []
        total_spend = 0
        total_conv = 0
        
        for r in results:
            spend = float(r.spend or 0)
            conv = int(r.conversions or 0)
            clicks = int(r.clicks or 0)
            impressions = int(r.impressions or 0)
            
            total_spend += spend
            total_conv += conv
            
            roas = (conv * 50000 / spend * 100) if spend > 0 else 0 # Mock revenue: 50,000 KRW per conversion
            cpa = (spend / conv) if conv > 0 else spend
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cvr = (conv / clicks * 100) if clicks > 0 else 0
            
            items.append({
                "name": f"[{r.platform.value}] {r.name}",
                "spend": spend,
                "conversions": conv,
                "clicks": clicks,
                "roas": round(roas, 1),
                "cpa": round(cpa, 0),
                "ctr": round(ctr, 2),
                "cvr": round(cvr, 2)
            })
            
        overall_roas = (total_conv * 50000 / total_spend * 100) if total_spend > 0 else 0
        
        period_start_str = actual_period[0].strftime("%Y-%m-%d") if actual_period and actual_period[0] else None
        period_end_str = actual_period[1].strftime("%Y-%m-%d") if actual_period and actual_period[1] else None

        return {
            "items": items,
            "overall_roas": round(overall_roas, 1),
            "total_spend": total_spend,
            "total_conversions": total_conv,
            "period": f"{period_start_str} ~ {period_end_str}" if period_start_str else f"최근 {days}일 (데이터 없음)",
            "period_start": period_start_str,
            "period_end": period_end_str
        }

    def seed_sample_metrics(self, client_id: str):
        """Seeds realistic sample advertising metrics for a client for demonstration purposes."""
        from uuid import uuid4
        from app.models.models import PlatformConnection, Campaign, MetricsDaily, PlatformType
        import random
        
        # 1. Ensure a connection exists
        conn = self.db.query(PlatformConnection).filter(PlatformConnection.client_id == client_id).first()
        if not conn:
            conn = PlatformConnection(
                id=uuid4(),
                client_id=client_id,
                platform=PlatformType.NAVER_AD,
                credentials={"sample": "true"},
                status="ACTIVE"
            )
            self.db.add(conn)
            self.db.flush()
        
        # 2. Ensure campaigns exist
        campaigns = self.db.query(Campaign).filter(Campaign.connection_id == conn.id).all()
        if not campaigns:
            camp_names = ["브랜드_임플란트_키워드", "지역_치아교정_전략", "디스플레이_타겟팅_리마케팅"]
            for name in camp_names:
                c = Campaign(id=uuid4(), connection_id=conn.id, external_id=f"sample_{random.randint(1000, 9999)}", name=name)
                self.db.add(c)
            self.db.flush()
            campaigns = self.db.query(Campaign).filter(Campaign.connection_id == conn.id).all()
            
        # 3. Seed metrics for last 30 days
        # We seed for both RECONCILED and API sources to ensure visibility with the new fallback logic
        for source in ['RECONCILED', 'API']:
            # Check if data already exists to avoid duplicates
            exists = self.db.query(MetricsDaily).join(Campaign).filter(Campaign.connection_id == conn.id, MetricsDaily.source == source).first()
            if exists: continue
            
            for i in range(30):
                date = datetime.date.today() - datetime.timedelta(days=i)
                for camp in campaigns:
                    spend = random.uniform(10000, 50000)
                    clicks = random.randint(50, 200)
                    conv = random.randint(1, 10)
                    rev = conv * 150000
                    
                    metric = MetricsDaily(
                        id=uuid4(),
                        campaign_id=camp.id,
                        date=date,
                        spend=spend,
                        clicks=clicks,
                        impressions=clicks * random.randint(10, 50),
                        conversions=conv,
                        revenue=rev,
                        source=source
                    )
                    self.db.add(metric)
        
        self.db.commit()
        return True
