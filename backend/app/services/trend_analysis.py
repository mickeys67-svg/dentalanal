from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from app.models.models import DailyRank, Keyword, MetricsDaily, Campaign, PlatformConnection, Notification
from typing import List, Dict, Optional, Tuple
from uuid import UUID, uuid4
import datetime
import logging
import statistics
from collections import defaultdict
import calendar

class TrendAnalysisService:
    """
    트렌드 분석 서비스

    주요 기능:
    1. 계절성 패턴 감지 (월별, 요일별)
    2. 검색 트렌드 예측
    3. 실시간 알림 시스템
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def detect_seasonality(
        self,
        client_id: UUID,
        lookback_months: int = 12
    ) -> Dict:
        """
        계절성 패턴 감지

        분석 항목:
        1. 월별 성과 변화 (MoM Growth)
        2. 요일별 성과 패턴
        3. 피크 시즌 식별

        Args:
            client_id: 클라이언트 ID
            lookback_months: 분석 기간 (개월)

        Returns:
            계절성 패턴 분석 결과
        """
        start_date = datetime.date.today() - datetime.timedelta(days=lookback_months * 30)

        # 1. 월별 성과 집계
        monthly_performance = self.db.query(
            extract('year', MetricsDaily.date).label('year'),
            extract('month', MetricsDaily.date).label('month'),
            func.sum(MetricsDaily.spend).label('spend'),
            func.sum(MetricsDaily.clicks).label('clicks'),
            func.sum(MetricsDaily.conversions).label('conversions'),
            func.sum(MetricsDaily.impressions).label('impressions')
        ).join(Campaign, MetricsDaily.campaign_id == Campaign.id)\
         .join(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
         .filter(
            and_(
                PlatformConnection.client_id == client_id,
                MetricsDaily.date >= start_date,
                MetricsDaily.source == 'RECONCILED'
            )
        ).group_by(
            extract('year', MetricsDaily.date),
            extract('month', MetricsDaily.date)
        ).order_by('year', 'month').all()

        monthly_data = []
        prev_spend = None

        for mp in monthly_performance:
            year = int(mp.year)
            month = int(mp.month)
            spend = float(mp.spend or 0)
            conversions = int(mp.conversions or 0)
            clicks = int(mp.clicks or 0)

            # MoM Growth 계산
            mom_growth = None
            if prev_spend is not None and prev_spend > 0:
                mom_growth = ((spend - prev_spend) / prev_spend) * 100

            monthly_data.append({
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month],
                "spend": spend,
                "clicks": clicks,
                "conversions": conversions,
                "mom_growth": round(mom_growth, 1) if mom_growth is not None else None
            })

            prev_spend = spend

        # 2. 요일별 성과 집계
        dow_performance = self.db.query(
            extract('dow', MetricsDaily.date).label('dow'),  # 0=Sunday, 6=Saturday
            func.sum(MetricsDaily.spend).label('spend'),
            func.sum(MetricsDaily.clicks).label('clicks'),
            func.sum(MetricsDaily.conversions).label('conversions')
        ).join(Campaign, MetricsDaily.campaign_id == Campaign.id)\
         .join(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
         .filter(
            and_(
                PlatformConnection.client_id == client_id,
                MetricsDaily.date >= start_date,
                MetricsDaily.source == 'RECONCILED'
            )
        ).group_by(extract('dow', MetricsDaily.date)).all()

        dow_map = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]
        dow_data = []

        for dp in dow_performance:
            dow_idx = int(dp.dow)
            dow_data.append({
                "day_of_week": dow_map[dow_idx],
                "spend": float(dp.spend or 0),
                "clicks": int(dp.clicks or 0),
                "conversions": int(dp.conversions or 0)
            })

        # 요일별 정렬 (월요일부터)
        dow_data.sort(key=lambda x: dow_map.index(x["day_of_week"]))

        # 3. 피크 시즌 식별 (상위 3개월)
        if monthly_data:
            sorted_months = sorted(monthly_data, key=lambda x: x["conversions"], reverse=True)
            peak_seasons = sorted_months[:3]
        else:
            peak_seasons = []

        # 4. 트렌드 분석 (상승/하락)
        if len(monthly_data) >= 3:
            recent_months = monthly_data[-3:]
            avg_growth = statistics.mean([m["mom_growth"] for m in recent_months if m["mom_growth"] is not None])
            trend = "상승" if avg_growth > 5 else "하락" if avg_growth < -5 else "안정"
        else:
            avg_growth = None
            trend = "데이터 부족"

        return {
            "analysis_period": f"{start_date} ~ {datetime.date.today()}",
            "monthly_performance": monthly_data,
            "dow_performance": dow_data,
            "peak_seasons": peak_seasons,
            "trend_summary": {
                "direction": trend,
                "avg_mom_growth": round(avg_growth, 1) if avg_growth is not None else None
            }
        }

    def predict_search_trends(
        self,
        client_id: UUID,
        keyword_id: Optional[UUID] = None,
        days: int = 90
    ) -> Dict:
        """
        검색 트렌드 예측

        Simple Moving Average (SMA) 기반 단순 예측 모델
        실제 운영에서는 ARIMA, Prophet 등 고급 모델 사용 권장

        Args:
            client_id: 클라이언트 ID
            keyword_id: 특정 키워드 ID (None이면 전체)
            days: 분석 기간

        Returns:
            검색 트렌드 예측 결과
        """
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)

        # 키워드별 일일 등장 횟수 추적
        query = self.db.query(
            func.date(DailyRank.captured_at).label('date'),
            Keyword.term,
            func.count(DailyRank.id).label('appearances'),
            func.avg(DailyRank.rank).label('avg_rank')
        ).join(Keyword, DailyRank.keyword_id == Keyword.id)\
         .filter(
            and_(
                Keyword.client_id == client_id,
                DailyRank.captured_at >= start_date
            )
        )

        if keyword_id:
            query = query.filter(Keyword.id == keyword_id)

        query = query.group_by(
            func.date(DailyRank.captured_at),
            Keyword.term
        ).order_by('date')

        results = query.all()

        # 키워드별 데이터 그룹화
        keyword_trends: Dict[str, List[Dict]] = defaultdict(list)

        for r in results:
            keyword_trends[r.term].append({
                "date": str(r.date),
                "appearances": r.appearances,
                "avg_rank": round(r.avg_rank, 1)
            })

        # 각 키워드별로 Simple Moving Average 계산 (7일)
        predictions = {}

        for keyword, trend_data in keyword_trends.items():
            if len(trend_data) < 7:
                continue

            # 최근 7일 평균
            recent_avg = statistics.mean([d["appearances"] for d in trend_data[-7:]])

            # 전체 평균
            overall_avg = statistics.mean([d["appearances"] for d in trend_data])

            # 예측 방향
            if recent_avg > overall_avg * 1.2:
                prediction = "상승 추세"
            elif recent_avg < overall_avg * 0.8:
                prediction = "하락 추세"
            else:
                prediction = "안정 추세"

            predictions[keyword] = {
                "trend_data": trend_data,
                "recent_avg": round(recent_avg, 1),
                "overall_avg": round(overall_avg, 1),
                "prediction": prediction
            }

        return {
            "analysis_period": f"{start_date.date()} ~ {datetime.date.today()}",
            "predictions": predictions
        }

    def create_ranking_drop_alert(
        self,
        client_id: UUID,
        rank_drop_threshold: int = 5
    ) -> List[Dict]:
        """
        순위 급락 알림

        전일 대비 순위가 {rank_drop_threshold}위 이상 하락한 키워드 감지

        Args:
            client_id: 클라이언트 ID
            rank_drop_threshold: 순위 하락 임계값 (기본 5위)

        Returns:
            순위 급락 키워드 목록
        """
        # 최근 2일간 데이터 조회
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        # 어제 순위
        yesterday_ranks = self.db.query(
            Keyword.id,
            Keyword.term,
            func.min(DailyRank.rank).label('rank')
        ).join(DailyRank, DailyRank.keyword_id == Keyword.id)\
         .filter(
            and_(
                Keyword.client_id == client_id,
                func.date(DailyRank.captured_at) == yesterday
            )
        ).group_by(Keyword.id, Keyword.term).all()

        # 그저께 순위
        two_days_ago_ranks = self.db.query(
            Keyword.id,
            func.min(DailyRank.rank).label('rank')
        ).join(DailyRank, DailyRank.keyword_id == Keyword.id)\
         .filter(
            and_(
                Keyword.client_id == client_id,
                func.date(DailyRank.captured_at) == two_days_ago
            )
        ).group_by(Keyword.id).all()

        # 그저께 순위 맵핑
        prev_rank_map = {r.id: r.rank for r in two_days_ago_ranks}

        # 순위 급락 감지
        drops = []

        for yr in yesterday_ranks:
            if yr.id in prev_rank_map:
                prev_rank = prev_rank_map[yr.id]
                curr_rank = yr.rank

                # 순위 하락 계산 (숫자가 커지면 하락)
                rank_change = curr_rank - prev_rank

                if rank_change >= rank_drop_threshold:
                    drops.append({
                        "keyword_id": str(yr.id),
                        "keyword": yr.term,
                        "previous_rank": prev_rank,
                        "current_rank": curr_rank,
                        "drop": rank_change
                    })

                    # 알림 생성
                    notification = Notification(
                        id=uuid4(),
                        client_id=client_id,
                        type="ALERT",
                        title=f"📉 순위 급락: {yr.term}",
                        message=f"'{yr.term}' 키워드가 {prev_rank}위에서 {curr_rank}위로 {rank_change}위 하락했습니다.",
                        is_read=False
                    )
                    self.db.add(notification)

        if drops:
            self.db.commit()
            self.logger.info(f"Created {len(drops)} ranking drop alerts for client {client_id}")

        return drops

    def create_budget_overspend_alert(
        self,
        client_id: UUID,
        monthly_budget_limit: Optional[float] = None
    ) -> Optional[Dict]:
        """
        예산 초과 알림

        월 예산 대비 현재 소진율 체크

        Args:
            client_id: 클라이언트 ID
            monthly_budget_limit: 월 예산 한도 (None이면 자동 계산)

        Returns:
            예산 초과 정보 (초과하지 않으면 None)
        """
        # 이번 달 시작일
        today = datetime.date.today()
        month_start = today.replace(day=1)

        # 이번 달 누적 광고비
        total_spend = self.db.query(
            func.sum(MetricsDaily.spend)
        ).join(Campaign, MetricsDaily.campaign_id == Campaign.id)\
         .join(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
         .filter(
            and_(
                PlatformConnection.client_id == client_id,
                MetricsDaily.date >= month_start,
                MetricsDaily.source == 'RECONCILED'
            )
        ).scalar()

        total_spend = float(total_spend or 0)

        # 월 예산 한도 자동 계산 (지난 3개월 평균)
        if monthly_budget_limit is None:
            three_months_ago = today - datetime.timedelta(days=90)

            avg_monthly_spend = self.db.query(
                func.avg(func.sum(MetricsDaily.spend))
            ).join(Campaign, MetricsDaily.campaign_id == Campaign.id)\
             .join(PlatformConnection, Campaign.connection_id == PlatformConnection.id)\
             .filter(
                and_(
                    PlatformConnection.client_id == client_id,
                    MetricsDaily.date >= three_months_ago,
                    MetricsDaily.date < month_start,
                    MetricsDaily.source == 'RECONCILED'
                )
            ).group_by(
                extract('year', MetricsDaily.date),
                extract('month', MetricsDaily.date)
            ).scalar()

            monthly_budget_limit = float(avg_monthly_spend or 0) * 1.1  # 10% 여유

        if monthly_budget_limit <= 0:
            return None

        # 소진율 계산
        utilization_rate = (total_spend / monthly_budget_limit) * 100

        # 80% 이상이면 경고
        if utilization_rate >= 80:
            severity = "high" if utilization_rate >= 100 else "medium"

            # 알림 생성
            notification = Notification(
                id=uuid4(),
                client_id=client_id,
                type="ALERT",
                title=f"💰 예산 {'초과' if utilization_rate >= 100 else '경고'}: {round(utilization_rate, 1)}%",
                message=f"이번 달 광고비가 {round(total_spend, 0):,.0f}원으로 예산 대비 {round(utilization_rate, 1)}% 소진되었습니다.",
                is_read=False
            )
            self.db.add(notification)
            self.db.commit()

            return {
                "total_spend": total_spend,
                "budget_limit": monthly_budget_limit,
                "utilization_rate": round(utilization_rate, 1),
                "severity": severity,
                "month": f"{today.year}-{today.month:02d}"
            }

        return None
