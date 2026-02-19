from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.models import MetricsDaily, Campaign, PlatformConnection, Notification, Client
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4
import datetime
import logging
import statistics

class ROIOptimizerService:
    """
    ROI 최적화 엔진

    주요 기능:
    1. 캠페인별 ROAS 추적 및 분석
    2. 비효율 광고 자동 감지
    3. 예산 재분배 추천
    """

    DEFAULT_CONVERSION_VALUE = 150000.0

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

        # 임계값 설정 (추후 클라이언트별 커스터마이징 가능)
        self.POOR_ROAS_THRESHOLD = 50  # ROAS 50% 이하
        self.LOW_CTR_THRESHOLD = 0.5   # CTR 0.5% 이하
        self.HIGH_CPA_PERCENTILE = 75  # CPA 상위 75% (비효율)
        self.MIN_SPEND_FOR_ANALYSIS = 50000  # 최소 광고비 5만원

    def _get_client_conversion_value(self, client_id: UUID) -> float:
        """클라이언트별 전환당 수익값 조회 (미설정 시 기본값 150,000원)"""
        try:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if client and client.conversion_value and client.conversion_value > 0:
                return float(client.conversion_value)
        except Exception:
            pass
        return self.DEFAULT_CONVERSION_VALUE

    def track_campaign_roas(
        self,
        client_id: UUID,
        days: int = 30,
        conversion_value: float = None  # None이면 클라이언트 설정값 또는 기본 150,000원
    ) -> Dict:
        """
        캠페인별 ROAS 추적 및 트렌드 분석

        Args:
            client_id: 클라이언트 ID
            days: 분석 기간
            conversion_value: 전환당 평균 수익 (기본 150,000원)

        Returns:
            캠페인별 ROAS 데이터 및 트렌드
        """
        if conversion_value is None:
            conversion_value = self._get_client_conversion_value(client_id)
        start_date = datetime.date.today() - datetime.timedelta(days=days)

        # 1. 캠페인별 전체 성과 집계
        campaigns_performance = self.db.query(
            Campaign.id,
            Campaign.name,
            PlatformConnection.platform,
            func.sum(MetricsDaily.spend).label("total_spend"),
            func.sum(MetricsDaily.clicks).label("total_clicks"),
            func.sum(MetricsDaily.conversions).label("total_conversions"),
            func.sum(MetricsDaily.impressions).label("total_impressions")
        ).join(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
         .join(MetricsDaily, MetricsDaily.campaign_id == Campaign.id)\
         .filter(
            and_(
                PlatformConnection.client_id == client_id,
                MetricsDaily.date >= start_date,
                MetricsDaily.source == 'RECONCILED'
            )
        ).group_by(Campaign.id, Campaign.name, PlatformConnection.platform).all()

        campaigns_data = []
        for camp in campaigns_performance:
            spend = float(camp.total_spend or 0)
            conversions = int(camp.total_conversions or 0)
            clicks = int(camp.total_clicks or 0)
            impressions = int(camp.total_impressions or 0)

            revenue = conversions * conversion_value
            roas = (revenue / spend * 100) if spend > 0 else 0
            cpa = (spend / conversions) if conversions > 0 else spend
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cvr = (conversions / clicks * 100) if clicks > 0 else 0

            # 2. 일별 트렌드 데이터
            daily_trend = self.db.query(
                MetricsDaily.date,
                func.sum(MetricsDaily.spend).label("spend"),
                func.sum(MetricsDaily.conversions).label("conversions")
            ).filter(
                and_(
                    MetricsDaily.campaign_id == camp.id,
                    MetricsDaily.date >= start_date,
                    MetricsDaily.source == 'RECONCILED'
                )
            ).group_by(MetricsDaily.date)\
             .order_by(MetricsDaily.date).all()

            trend_data = [{
                "date": str(d.date),
                "roas": (d.conversions * conversion_value / d.spend * 100) if d.spend > 0 else 0
            } for d in daily_trend]

            campaigns_data.append({
                "campaign_id": str(camp.id),
                "campaign_name": camp.name,
                "platform": camp.platform.value,
                "total_spend": spend,
                "total_conversions": conversions,
                "roas": round(roas, 1),
                "cpa": round(cpa, 0),
                "ctr": round(ctr, 2),
                "cvr": round(cvr, 2),
                "trend": trend_data
            })

        # ROAS 높은 순으로 정렬
        campaigns_data.sort(key=lambda x: x["roas"], reverse=True)

        return {
            "period": f"{start_date} ~ {datetime.date.today()}",
            "campaigns": campaigns_data,
            "summary": {
                "total_campaigns": len(campaigns_data),
                "avg_roas": round(statistics.mean([c["roas"] for c in campaigns_data]), 1) if campaigns_data else 0,
                "best_performer": campaigns_data[0]["campaign_name"] if campaigns_data else None,
                "worst_performer": campaigns_data[-1]["campaign_name"] if campaigns_data else None
            }
        }

    def detect_inefficient_ads(
        self,
        client_id: UUID,
        days: int = 30,
        conversion_value: float = None
    ) -> List[Dict]:
        """
        비효율 광고 자동 감지

        감지 기준:
        1. ROAS가 임계값(50%) 이하
        2. CTR이 업종 평균(0.5%) 이하
        3. CPA가 상위 75% 이상 (동일 클라이언트 내 비교)

        Args:
            client_id: 클라이언트 ID
            days: 분석 기간
            conversion_value: 전환당 평균 수익

        Returns:
            비효율 광고 목록 및 개선 권장사항
        """
        if conversion_value is None:
            conversion_value = self._get_client_conversion_value(client_id)
        start_date = datetime.date.today() - datetime.timedelta(days=days)

        # 캠페인별 성과 집계
        campaigns = self.db.query(
            Campaign.id,
            Campaign.name,
            PlatformConnection.platform,
            func.sum(MetricsDaily.spend).label("spend"),
            func.sum(MetricsDaily.clicks).label("clicks"),
            func.sum(MetricsDaily.conversions).label("conversions"),
            func.sum(MetricsDaily.impressions).label("impressions")
        ).join(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
         .join(MetricsDaily, MetricsDaily.campaign_id == Campaign.id)\
         .filter(
            and_(
                PlatformConnection.client_id == client_id,
                MetricsDaily.date >= start_date,
                MetricsDaily.source == 'RECONCILED'
            )
        ).group_by(Campaign.id, Campaign.name, PlatformConnection.platform)\
         .having(func.sum(MetricsDaily.spend) >= self.MIN_SPEND_FOR_ANALYSIS)\
         .all()

        # CPA 분포 계산 (75분위수)
        cpa_list = []
        campaign_metrics = {}

        for camp in campaigns:
            spend = float(camp.spend or 0)
            conversions = int(camp.conversions or 0)
            clicks = int(camp.clicks or 0)
            impressions = int(camp.impressions or 0)

            cpa = (spend / conversions) if conversions > 0 else float('inf')
            cpa_list.append(cpa if cpa != float('inf') else 0)

            campaign_metrics[camp.id] = {
                "name": camp.name,
                "platform": camp.platform.value,
                "spend": spend,
                "conversions": conversions,
                "clicks": clicks,
                "impressions": impressions,
                "cpa": cpa
            }

        # 비효율 광고 필터링
        inefficient_ads = []
        cpa_threshold = statistics.quantile(cpa_list, 0.75) if len(cpa_list) >= 4 else float('inf')

        for camp_id, metrics in campaign_metrics.items():
            spend = metrics["spend"]
            conversions = metrics["conversions"]
            clicks = metrics["clicks"]
            impressions = metrics["impressions"]
            cpa = metrics["cpa"]

            revenue = conversions * conversion_value
            roas = (revenue / spend * 100) if spend > 0 else 0
            ctr = (clicks / impressions * 100) if impressions > 0 else 0

            issues = []
            severity = "low"

            # 1. ROAS 체크
            if roas < self.POOR_ROAS_THRESHOLD:
                issues.append(f"ROAS가 {round(roas, 1)}%로 목표({self.POOR_ROAS_THRESHOLD}%) 미달")
                severity = "high"

            # 2. CTR 체크
            if ctr < self.LOW_CTR_THRESHOLD:
                issues.append(f"CTR이 {round(ctr, 2)}%로 업종 평균({self.LOW_CTR_THRESHOLD}%) 미달")
                if severity != "high":
                    severity = "medium"

            # 3. CPA 체크
            if cpa != float('inf') and cpa >= cpa_threshold:
                issues.append(f"CPA가 {round(cpa, 0)}원으로 클라이언트 평균 대비 높음")
                if severity == "low":
                    severity = "medium"

            if issues:
                # 개선 권장사항 생성
                recommendations = self._generate_recommendations(roas, ctr, cpa, cpa_threshold)

                inefficient_ads.append({
                    "campaign_id": str(camp_id),
                    "campaign_name": metrics["name"],
                    "platform": metrics["platform"],
                    "spend": spend,
                    "roas": round(roas, 1),
                    "ctr": round(ctr, 2),
                    "cpa": round(cpa, 0) if cpa != float('inf') else None,
                    "severity": severity,
                    "issues": issues,
                    "recommendations": recommendations
                })

        # 심각도 순으로 정렬
        severity_order = {"high": 3, "medium": 2, "low": 1}
        inefficient_ads.sort(key=lambda x: severity_order.get(x["severity"], 0), reverse=True)

        return inefficient_ads

    def _generate_recommendations(
        self,
        roas: float,
        ctr: float,
        cpa: float,
        cpa_threshold: float
    ) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []

        if roas < self.POOR_ROAS_THRESHOLD:
            recommendations.append("전환율 개선을 위해 타겟팅 및 키워드를 재검토하세요")
            recommendations.append("랜딩 페이지 최적화로 전환율을 높이세요")

        if ctr < self.LOW_CTR_THRESHOLD:
            recommendations.append("광고 소재(제목, 이미지)를 A/B 테스트하세요")
            recommendations.append("더 구체적이고 매력적인 문구로 변경하세요")

        if cpa != float('inf') and cpa >= cpa_threshold:
            recommendations.append("일일 예산을 줄이거나 일시 중지를 고려하세요")
            recommendations.append("입찰가를 낮추어 CPA를 개선하세요")

        return recommendations

    def recommend_budget_reallocation(
        self,
        client_id: UUID,
        days: int = 30,
        conversion_value: float = None
    ) -> Dict:
        """
        예산 재분배 추천

        알고리즘:
        1. ROAS 상위 20% 캠페인: 예산 증액 권장
        2. ROAS 하위 20% 캠페인: 예산 감액 권장
        3. 중간 캠페인: 유지 권장

        Returns:
            예산 재분배 계획
        """
        # ROAS 추적 데이터 가져오기
        roas_data = self.track_campaign_roas(client_id, days, conversion_value)
        campaigns = roas_data["campaigns"]

        if len(campaigns) < 3:
            return {
                "message": "분석을 위한 충분한 캠페인 데이터가 없습니다 (최소 3개 필요)",
                "recommendations": []
            }

        # 총 예산 계산
        total_budget = sum(c["total_spend"] for c in campaigns)

        # ROAS 기준 정렬 (이미 정렬되어 있음)
        top_20_count = max(1, len(campaigns) // 5)
        bottom_20_count = max(1, len(campaigns) // 5)

        recommendations = []

        # 상위 20%: 예산 증액
        for camp in campaigns[:top_20_count]:
            increase_amount = camp["total_spend"] * 0.2  # 20% 증액
            recommendations.append({
                "campaign_name": camp["campaign_name"],
                "current_spend": camp["total_spend"],
                "recommended_spend": camp["total_spend"] + increase_amount,
                "change": f"+{round(increase_amount, 0)}원 (+20%)",
                "action": "증액",
                "reason": f"ROAS {camp['roas']}%로 우수한 성과",
                "roas": camp["roas"]
            })

        # 하위 20%: 예산 감액
        for camp in campaigns[-bottom_20_count:]:
            if camp["roas"] < self.POOR_ROAS_THRESHOLD:
                decrease_amount = camp["total_spend"] * 0.3  # 30% 감액
                recommendations.append({
                    "campaign_name": camp["campaign_name"],
                    "current_spend": camp["total_spend"],
                    "recommended_spend": max(0, camp["total_spend"] - decrease_amount),
                    "change": f"-{round(decrease_amount, 0)}원 (-30%)",
                    "action": "감액",
                    "reason": f"ROAS {camp['roas']}%로 비효율적",
                    "roas": camp["roas"]
                })

        # 재분배 후 총 예산 (증액분 - 감액분)
        total_increase = sum(r["recommended_spend"] - r["current_spend"] for r in recommendations if r["action"] == "증액")
        total_decrease = sum(r["current_spend"] - r["recommended_spend"] for r in recommendations if r["action"] == "감액")

        return {
            "period": roas_data["period"],
            "current_total_budget": total_budget,
            "recommended_total_budget": total_budget + total_increase - total_decrease,
            "net_change": total_increase - total_decrease,
            "recommendations": recommendations,
            "summary": {
                "campaigns_to_increase": sum(1 for r in recommendations if r["action"] == "증액"),
                "campaigns_to_decrease": sum(1 for r in recommendations if r["action"] == "감액"),
                "total_increase_amount": round(total_increase, 0),
                "total_decrease_amount": round(total_decrease, 0)
            }
        }

    def create_alert_for_inefficiency(
        self,
        client_id: UUID,
        inefficient_ads: List[Dict]
    ) -> None:
        """
        비효율 광고 감지 시 알림 생성

        Args:
            client_id: 클라이언트 ID
            inefficient_ads: 비효율 광고 목록
        """
        if not inefficient_ads:
            return

        high_severity = [ad for ad in inefficient_ads if ad["severity"] == "high"]

        if high_severity:
            # 심각한 비효율 광고에 대한 알림 생성
            for ad in high_severity[:3]:  # 최대 3개만
                notification = Notification(
                    id=uuid4(),
                    client_id=client_id,
                    type="ALERT",
                    title=f"⚠️ 비효율 광고 감지: {ad['campaign_name']}",
                    message=f"ROAS {ad['roas']}%로 매우 낮은 성과를 보이고 있습니다. {', '.join(ad['recommendations'][:2])}",
                    is_read=False
                )
                self.db.add(notification)

            self.db.commit()
            self.logger.info(f"Created {len(high_severity)} inefficiency alerts for client {client_id}")
