import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import MetricsDaily, Campaign, PlatformConnection, AnalysisHistory, Client
import datetime

logger = logging.getLogger(__name__)

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _get_client_conversion_value(self, client_id) -> float:
        """클라이언트별 전환당 수익값 조회 (미설정 시 기본값 150,000원)"""
        DEFAULT_CONVERSION_VALUE = 150000.0
        if not client_id:
            return DEFAULT_CONVERSION_VALUE
        try:
            from uuid import UUID
            cid = UUID(str(client_id)) if not isinstance(client_id, UUID) else client_id
            client = self.db.query(Client).filter(Client.id == cid).first()
            if client and client.conversion_value and client.conversion_value > 0:
                return float(client.conversion_value)
        except Exception:
            pass
        return DEFAULT_CONVERSION_VALUE

    def _get_client_fee_rate(self, client_id) -> float:
        """클라이언트별 수수료율 조회 (미설정 시 기본값 15%)"""
        DEFAULT_FEE_RATE = 0.15
        if not client_id:
            return DEFAULT_FEE_RATE
        try:
            from uuid import UUID
            cid = UUID(str(client_id)) if not isinstance(client_id, UUID) else client_id
            client = self.db.query(Client).filter(Client.id == cid).first()
            if client and client.fee_rate and 0 < client.fee_rate <= 1:
                return float(client.fee_rate)
        except Exception:
            pass
        return DEFAULT_FEE_RATE

    def get_summary_metrics(self, client_id: str = None) -> Dict[str, Any]:
        """
        Fetch aggregated metrics and calculate KPIs.
        """
        logger.info(f"Generating summary metrics for client_id: {client_id}")
        try:
            # Determine best source (Fallback: RECONCILED > API > SCRAPER)
            source_filter = 'RECONCILED'
            recon_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'RECONCILED').limit(1).first()
            if not recon_exists:
                api_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'API').limit(1).first()
                source_filter = 'API' if api_exists else 'SCRAPER'
                logger.warning(f"No RECONCILED metrics found. Using {source_filter} fallback.")

            # KPI Query with Explicit Joins
            query = self.db.query(
                func.sum(MetricsDaily.spend).label("total_spend"),
                func.sum(MetricsDaily.clicks).label("total_clicks"),
                func.sum(MetricsDaily.impressions).label("total_impressions"),
                func.sum(MetricsDaily.conversions).label("total_conversions")
            ).filter(MetricsDaily.source == source_filter)
            
            if client_id:
                query = query.join(Campaign, Campaign.id == MetricsDaily.campaign_id)\
                             .join(PlatformConnection, PlatformConnection.id == Campaign.connection_id)\
                             .filter(PlatformConnection.client_id == client_id)
            
            results = query.first()
            
            # Safe extraction
            total_spend = float(results.total_spend or 0) if results and hasattr(results, 'total_spend') else 0.0
            total_clicks = int(results.total_clicks or 0) if results and hasattr(results, 'total_clicks') else 0
            total_conversions = int(results.total_conversions or 0) if results and hasattr(results, 'total_conversions') else 0
            total_impressions = int(results.total_impressions or 0) if results and hasattr(results, 'total_impressions') else 0
            
            logger.debug(f"KPIs - Spend: {total_spend}, Conversions: {total_conversions}")

            # Revenue Query with Explicit Joins
            revenue_query = self.db.query(func.sum(MetricsDaily.revenue).label("total_revenue")).filter(MetricsDaily.source == source_filter)
            if client_id:
                revenue_query = revenue_query.join(Campaign, Campaign.id == MetricsDaily.campaign_id)\
                                             .join(PlatformConnection, PlatformConnection.id == Campaign.connection_id)\
                                             .filter(PlatformConnection.client_id == client_id)
            
            revenue_res = revenue_query.first()
            total_revenue = float(revenue_res.total_revenue or 0) if revenue_res and hasattr(revenue_res, 'total_revenue') else 0.0
            
            if total_revenue == 0 and total_conversions > 0:
                conversion_value = self._get_client_conversion_value(client_id)
                total_revenue = total_conversions * conversion_value
                
            avg_roas = (total_revenue / total_spend * 100) if total_spend > 0 else 0
            avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

            # SOV Data
            platforms_query = self.db.query(
                PlatformConnection.platform,
                func.sum(MetricsDaily.spend).label("spend")
            ).join(Campaign, Campaign.id == MetricsDaily.campaign_id)\
             .join(PlatformConnection, PlatformConnection.id == Campaign.connection_id)
            
            if client_id:
                platforms_query = platforms_query.filter(PlatformConnection.client_id == client_id)
                
            platforms_results = platforms_query.group_by(PlatformConnection.platform).all()
            total_sov_spend = sum(float(r.spend or 0) for r in platforms_results)
            
            sov_data = []
            if platforms_results:
                for r in platforms_results:
                    share = (float(r.spend or 0) / total_sov_spend * 100) if total_sov_spend > 0 else 0
                    sov_data.append({
                        "name": r.platform.value if hasattr(r.platform, 'value') else str(r.platform),
                        "value": round(share, 1)
                    })

            is_sample = False
            if not sov_data:
                # No longer using mock SOV data. 
                # Front-end should handle empty state.
                sov_data = []

            # Get last keyword
            last_keyword = "치과"
            if client_id:
                history = self.db.query(AnalysisHistory).filter(AnalysisHistory.client_id == client_id).order_by(AnalysisHistory.created_at.desc()).first()
                if history:
                    last_keyword = history.keyword

            return {
                "kpis": [
                    {"title": "총 광고 집행비", "value": int(total_spend), "change": 0.0, "prefix": "₩"},
                    {"title": "평균 ROAS", "value": int(avg_roas), "change": 0.0, "suffix": "%"},
                    {"title": "총 전환수", "value": total_conversions, "change": 0.0},
                    {"title": "평균 CPC", "value": int(avg_cpc), "change": 0.0, "prefix": "₩"}
                ],
                "campaigns": self.get_top_campaigns(client_id),
                "sov_data": sov_data,
                "last_keyword": last_keyword,
                "is_sample": is_sample
            }
        except Exception as e:
            logger.error(f"Failed to get_summary_metrics: {str(e)}")
            raise

    def get_top_campaigns(self, client_id: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Fetching top campaigns for client_id: {client_id}")
        try:
            # Determine best source
            source_filter = 'RECONCILED'
            recon_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'RECONCILED').limit(1).first()
            if not recon_exists:
                api_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'API').limit(1).first()
                source_filter = 'API' if api_exists else 'SCRAPER'

            query = self.db.query(
                Campaign.name,
                PlatformConnection.platform,
                func.sum(MetricsDaily.spend).label("spend"),
                func.sum(MetricsDaily.conversions).label("conversions")
            ).outerjoin(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
             .outerjoin(MetricsDaily, (MetricsDaily.campaign_id == Campaign.id) & (MetricsDaily.source == source_filter))
            
            if client_id:
                query = query.filter(PlatformConnection.client_id == client_id)
                
            results = query.group_by(Campaign.id, Campaign.name, PlatformConnection.platform)\
                           .order_by(func.sum(MetricsDaily.spend).desc())\
                           .limit(limit).all()
            
            conversion_value = self._get_client_conversion_value(client_id)
            campaigns = []
            for r in results:
                rev = (int(r.conversions or 0) * conversion_value)
                roas = (rev / float(r.spend or 1) * 100) if float(r.spend or 0) > 0 else 0
                campaigns.append({
                    "name": r.name,
                    "platform": r.platform.value if hasattr(r.platform, 'value') else str(r.platform),
                    "spend": int(r.spend or 0),
                    "roas": round(roas, 1),
                    "conversions": int(r.conversions or 0)
                })
                
            # 캠페인 데이터가 없을 경우 하드코딩된 mock을 제거하고 빈 배열 반환 가능
            # 여기서는 명시적으로 빈 배열 반환 (is_sample 여부와 무관하게 실제가 없으면 없는 것)
            return campaigns
        except Exception as e:
            logger.error(f"Failed to get_top_campaigns: {str(e)}")
            return []

    def get_trend_data(self, client_id: str = None, days: int = 7) -> List[Dict[str, Any]]:
        logger.info(f"Fetching trend data for client_id: {client_id}")
        try:
            # Trend source fallback
            source_filter = 'RECONCILED'
            recon_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'RECONCILED').limit(1).first()
            if not recon_exists:
                api_exists = self.db.query(MetricsDaily.id).filter(MetricsDaily.source == 'API').limit(1).first()
                source_filter = 'API' if api_exists else 'SCRAPER'

            query = self.db.query(
                MetricsDaily.date,
                func.sum(MetricsDaily.spend).label("spend"),
                func.sum(MetricsDaily.clicks).label("clicks"),
                func.sum(MetricsDaily.conversions).label("conversions")
            ).filter(MetricsDaily.source == source_filter)

            if client_id:
                query = query.join(Campaign, Campaign.id == MetricsDaily.campaign_id)\
                             .join(PlatformConnection, PlatformConnection.id == Campaign.connection_id)\
                             .filter(PlatformConnection.client_id == client_id)
            
            results = query.group_by(MetricsDaily.date).order_by(MetricsDaily.date).all()
            
            trend = []
            for r in results:
                trend.append({
                    "date": r.date.strftime("%Y-%m-%d"),
                    "spend": float(r.spend or 0),
                    "clicks": int(r.clicks or 0),
                    "conversions": int(r.conversions or 0)
                })
                
            # 트렌드 데이터가 없을 경우 빈 배열 반환
            return trend
        except Exception as e:
            logger.error(f"Failed to get_trend_data: {str(e)}")
            return []
