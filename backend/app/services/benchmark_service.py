from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import MetricsDaily, Campaign, PlatformConnection, Client
from typing import List, Dict, Any
from uuid import UUID

class BenchmarkService:
    def __init__(self, db: Session):
        self.db = db

    def get_industry_averages(self, industry: str) -> Dict[str, Any]:
        """
        Calculate average KPIs for a specific industry across all clients.
        """
        if not industry:
            return {}

        # Aggregate metrics for all clients in the same industry
        results = self.db.query(
            func.sum(MetricsDaily.impressions).label("total_impressions"),
            func.sum(MetricsDaily.clicks).label("total_clicks"),
            func.sum(MetricsDaily.spend).label("total_spend"),
            func.sum(MetricsDaily.conversions).label("total_conversions")
        ).join(Campaign).join(PlatformConnection).join(Client).filter(
            Client.industry == industry
        ).first()

        if not results or not results.total_impressions:
            return {
                "avg_ctr": 0.0,
                "avg_cpc": 0.0,
                "avg_cvr": 0.0,
                "count": 0
            }

        total_imp = float(results.total_impressions)
        total_clicks = float(results.total_clicks)
        total_spend = float(results.total_spend)
        total_conv = float(results.total_conversions)

        avg_ctr = (total_clicks / total_imp * 100) if total_imp > 0 else 0
        avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
        avg_cvr = (total_conv / total_clicks * 100) if total_clicks > 0 else 0

        return {
            "avg_ctr": round(avg_ctr, 2),
            "avg_cpc": round(avg_cpc, 0),
            "avg_cvr": round(avg_cvr, 2),
            "industry": industry
        }

    def compare_client_performance(self, client_id: UUID) -> Dict[str, Any]:
        """
        Compare a client's performance against their industry average.
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"error": "Client not found"}

        # 1. Get Client's own averages
        client_metrics = self.db.query(
            func.sum(MetricsDaily.impressions).label("total_impressions"),
            func.sum(MetricsDaily.clicks).label("total_clicks"),
            func.sum(MetricsDaily.spend).label("total_spend"),
            func.sum(MetricsDaily.conversions).label("total_conversions")
        ).join(Campaign).join(PlatformConnection).filter(
            PlatformConnection.client_id == client_id
        ).first()

        c_imp = float(client_metrics.total_impressions or 0)
        c_clicks = float(client_metrics.total_clicks or 0)
        c_spend = float(client_metrics.total_spend or 0)
        c_conv = float(client_metrics.total_conversions or 0)

        client_kpis = {
            "ctr": round((c_clicks / c_imp * 100), 2) if c_imp > 0 else 0,
            "cpc": round((c_spend / c_clicks), 0) if c_clicks > 0 else 0,
            "cvr": round((c_conv / c_clicks * 100), 2) if c_clicks > 0 else 0
        }

        # 2. Get Industry Averages
        industry_avg = self.get_industry_averages(client.industry)

        # 3. Calculate Benchmarks (Difference / Percentage)
        return {
            "client_name": client.name,
            "industry": client.industry,
            "client_kpis": client_kpis,
            "industry_avg": industry_avg,
            "comparison": {
                "ctr_diff": round(client_kpis["ctr"] - industry_avg.get("avg_ctr", 0), 2),
                "cpc_diff": round(client_kpis["cpc"] - industry_avg.get("avg_cpc", 0), 0),
                "cvr_diff": round(client_kpis["cvr"] - industry_avg.get("avg_cvr", 0), 2)
            }
        }
