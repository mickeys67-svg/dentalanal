from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import MetricsDaily, Campaign, PlatformConnection
from typing import List, Dict, Any

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary_metrics(self, client_id: str = None) -> Dict[str, Any]:
        """
        Fetch aggregated metrics and calculate KPIs.
        """
        query = self.db.query(
            func.sum(MetricsDaily.spend).label("total_spend"),
            func.sum(MetricsDaily.clicks).label("total_clicks"),
            func.sum(MetricsDaily.impressions).label("total_impressions"),
            func.sum(MetricsDaily.conversions).label("total_conversions")
        )
        
        if client_id:
            query = query.outerjoin(Campaign).outerjoin(PlatformConnection).filter(PlatformConnection.client_id == client_id)
        
        results = query.first()
        
        # FIX: Check if results is None (occurs when no campaigns/connections found for client)
        if not results:
            total_spend = 0.0
            total_clicks = 0
            total_conversions = 0
            total_impressions = 0
        else:
            total_spend = float(results.total_spend or 0)
            total_clicks = int(results.total_clicks or 0)
            total_conversions = int(results.total_conversions or 0)
            total_impressions = int(results.total_impressions or 0)
        
        # Calculate ROAS and CPC (Fixed undefined variables)
        avg_roas = 0.0
        # In this simplified model, revenue is in MetricsDaily. 
        # For demo, let's assume a fixed conversion value if revenue is 0.
        revenue_query = self.db.query(func.sum(MetricsDaily.revenue).label("total_revenue"))
        if client_id:
            revenue_query = revenue_query.outerjoin(Campaign).outerjoin(PlatformConnection).filter(PlatformConnection.client_id == client_id)
        
        revenue_res = revenue_query.first()
        total_revenue = float(revenue_res.total_revenue or 0) if revenue_res else 0.0
        
        if total_revenue == 0 and total_conversions > 0:
            total_revenue = total_conversions * 150000 # Mock value: 15만원 per conversion
            
        avg_roas = (total_revenue / total_spend * 100) if total_spend > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

        # SOV Data
        platforms_query = self.db.query(
            PlatformConnection.platform,
            func.sum(MetricsDaily.spend).label("spend")
        ).outerjoin(Campaign).outerjoin(PlatformConnection).group_by(PlatformConnection.platform)
        
        if client_id:
            platforms_query = platforms_query.filter(PlatformConnection.client_id == client_id)
            
        platforms_results = platforms_query.all()
        total_sov_spend = sum(float(r.spend or 0) for r in platforms_results)
        
        sov_data = []
        if platforms_results:
            for r in platforms_results:
                share = (float(r.spend or 0) / total_sov_spend * 100) if total_sov_spend > 0 else 0
                sov_data.append({
                    "name": r.platform.value if hasattr(r.platform, 'value') else str(r.platform),
                    "value": round(share, 1)
                })

        if not sov_data:
            sov_data = [
                {"name": "네이버", "value": 60},
                {"name": "메타", "value": 30},
                {"name": "구글", "value": 10}
            ]

        return {
            "kpis": [
                {"title": "총 광고 집행비", "value": int(total_spend), "change": 15.6, "prefix": "₩"},
                {"title": "평균 ROAS", "value": int(avg_roas), "change": 12.3, "suffix": "%"},
                {"title": "총 전환수", "value": total_conversions, "change": 8.5},
                {"title": "평균 CPC", "value": int(avg_cpc), "change": -5.2, "prefix": "₩"}
            ],
            "campaigns": self.get_top_campaigns(client_id),
            "sov_data": sov_data
        }

    def get_top_campaigns(self, client_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch top campaigns with metrics.
        """
        query = self.db.query(
            Campaign.name,
            PlatformConnection.platform,
            func.sum(MetricsDaily.spend).label("spend"),
            func.sum(MetricsDaily.revenue).label("revenue"),
            func.sum(MetricsDaily.conversions).label("conversions")
        ).outerjoin(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
         .outerjoin(MetricsDaily, MetricsDaily.campaign_id == Campaign.id)\
         .group_by(Campaign.id, PlatformConnection.platform)\
         .order_by(func.sum(MetricsDaily.spend).desc())\
         .limit(limit)

        if client_id:
            query = query.filter(PlatformConnection.client_id == client_id)


        results = query.all()
        
        campaigns = []
        for r in results:
            spend = float(r.spend or 0)
            rev = float(r.revenue or 0)
            conv = int(r.conversions or 0)
            if rev == 0 and conv > 0: rev = conv * 150000
            
            roas = (rev / spend * 100) if spend > 0 else 0
            
            campaigns.append({
                "name": r.name,
                "platform": r.platform.value if hasattr(r.platform, 'value') else str(r.platform),
                "spend": int(spend),
                "roas": int(roas),
                "conversions": conv
            })
            
        if not campaigns:
            # Mock for empty DB
            campaigns = [
                {"name": "네이버 브랜드검색_치과", "platform": "NAVER_AD", "spend": 1200000, "roas": 520, "conversions": 45},
                {"name": "메타 리마케팅_임플란트", "platform": "META_ADS", "spend": 850000, "roas": 380, "conversions": 12}
            ]
            
        return campaigns

    def get_trend_data(self, client_id: str = None, days: int = 7) -> List[Dict[str, Any]]:
        import datetime
        query = self.db.query(
            MetricsDaily.date,
            func.sum(MetricsDaily.spend).label("spend"),
            func.sum(MetricsDaily.clicks).label("clicks"),
            func.sum(MetricsDaily.conversions).label("conversions")
        ).group_by(MetricsDaily.date).order_by(MetricsDaily.date)

        if client_id:
            query = query.join(Campaign).join(PlatformConnection).filter(PlatformConnection.client_id == client_id)

        results = query.all()
        
        trend = []
        for r in results:
            trend.append({
                "date": r.date.strftime("%Y-%m-%d"),
                "spend": float(r.spend or 0),
                "clicks": int(r.clicks or 0),
                "conversions": int(r.conversions or 0)
            })
            
        if not trend:
            today = datetime.date.today()
            for i in range(days, 0, -1):
                date = today - datetime.timedelta(days=i)
                trend.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "spend": 50000 + (i * 1000),
                    "clicks": 100 + (i * 10),
                    "conversions": 5 + (i % 3)
                })
        return trend
