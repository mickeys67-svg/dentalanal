from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.models import DailyRank, Target, Keyword, TargetType, PlatformType, MetricsDaily, Campaign
from typing import List, Dict, Optional, Tuple
from uuid import UUID
import logging
from collections import defaultdict, Counter
import datetime

class CompetitorIntelligenceService:
    """
    경쟁사 자동 발굴 및 인텔리전스 분석 서비스

    주요 기능:
    1. 키워드 중복도 기반 경쟁사 자동 발굴
    2. 경쟁사 광고 전략 분석
    3. 시장 포지셔닝 분석
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def discover_competitors(
        self,
        client_id: UUID,
        platform: PlatformType = PlatformType.NAVER_PLACE,
        keyword_overlap_threshold: float = 0.3,
        min_appearances: int = 3,
        top_n: int = 10,
        days: int = 30
    ) -> List[Dict]:
        """
        키워드 중복도 기반 경쟁사 자동 발굴

        알고리즘:
        1. 클라이언트가 추적 중인 키워드 목록 추출
        2. 해당 키워드들의 랭킹 데이터에서 자주 등장하는 타겟 식별
        3. 키워드 중복도 계산 (Jaccard Similarity)
        4. 중복도가 높은 타겟을 경쟁사로 분류

        Args:
            client_id: 분석 대상 클라이언트 ID
            platform: 분석 플랫폼 (NAVER_PLACE, NAVER_VIEW 등)
            keyword_overlap_threshold: 키워드 중복도 임계값 (0.0~1.0)
            min_appearances: 최소 등장 횟수 (이보다 적게 나타난 타겟은 제외)
            top_n: 상위 N개 경쟁사만 반환
            days: 분석 기간 (최근 N일)

        Returns:
            경쟁사 목록 (중복도 높은 순)
        """
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)

        # 1. 클라이언트가 추적 중인 키워드 목록 추출
        client_keywords = self.db.query(Keyword).filter(
            Keyword.client_id == client_id
        ).all()

        if not client_keywords:
            self.logger.warning(f"No keywords found for client {client_id}")
            return []

        keyword_ids = [kw.id for kw in client_keywords]
        keyword_terms = {kw.id: kw.term for kw in client_keywords}

        # 2. 해당 키워드들의 랭킹 데이터에서 타겟별 등장 횟수 및 키워드 집합 수집
        ranks = self.db.query(DailyRank).filter(
            and_(
                DailyRank.keyword_id.in_(keyword_ids),
                DailyRank.platform == platform,
                DailyRank.captured_at >= start_date,
                DailyRank.rank <= 20  # 상위 20위 이내만 고려
            )
        ).all()

        if not ranks:
            self.logger.warning(f"No ranking data found for client keywords")
            return []

        # 타겟별 등장한 키워드 집합 수집
        target_keywords: Dict[UUID, set] = defaultdict(set)
        target_info: Dict[UUID, Dict] = {}

        for rank in ranks:
            target_keywords[rank.target_id].add(rank.keyword_id)
            if rank.target_id not in target_info:
                target_info[rank.target_id] = {
                    "id": rank.target_id,
                    "name": rank.target.name,
                    "type": rank.target.type,
                    "urls": rank.target.urls
                }

        # 3. 키워드 중복도 계산 (Jaccard Similarity)
        # J(A,B) = |A ∩ B| / |A ∪ B|
        client_keyword_set = set(keyword_ids)
        competitors = []

        for target_id, target_kw_set in target_keywords.items():
            # 최소 등장 횟수 필터링
            if len(target_kw_set) < min_appearances:
                continue

            # Jaccard Similarity 계산
            intersection = len(client_keyword_set & target_kw_set)
            union = len(client_keyword_set | target_kw_set)
            overlap_score = intersection / union if union > 0 else 0

            # 임계값 이상인 경우만 경쟁사로 간주
            if overlap_score >= keyword_overlap_threshold:
                info = target_info[target_id]
                competitors.append({
                    "target_id": str(target_id),
                    "name": info["name"],
                    "type": info["type"].value,
                    "overlap_score": round(overlap_score, 3),
                    "shared_keywords": intersection,
                    "total_keywords": union,
                    "keywords_appeared": len(target_kw_set),
                    "shared_keyword_terms": [
                        keyword_terms[kw_id]
                        for kw_id in (client_keyword_set & target_kw_set)
                    ]
                })

        # 중복도 높은 순으로 정렬
        competitors.sort(key=lambda x: x["overlap_score"], reverse=True)

        return competitors[:top_n]

    def analyze_competitor_strategy(
        self,
        target_id: UUID,
        platform: PlatformType = PlatformType.NAVER_AD,
        days: int = 30
    ) -> Dict:
        """
        경쟁사 광고 전략 분석

        분석 항목:
        1. 활성 캠페인 수
        2. 평균 광고비 (일별)
        3. 주력 키워드 (랭킹 데이터 기반)
        4. 광고 집행 패턴 (요일별, 시간대별)
        5. 성과 지표 (CTR, CVR 추정)

        Args:
            target_id: 분석 대상 타겟(경쟁사) ID
            platform: 분석 플랫폼
            days: 분석 기간

        Returns:
            경쟁사 전략 분석 결과
        """
        start_date = datetime.date.today() - datetime.timedelta(days=days)

        # 타겟 정보 조회
        target = self.db.query(Target).filter(Target.id == target_id).first()
        if not target:
            raise ValueError(f"Target {target_id} not found")

        # 1. 랭킹 데이터 기반 주력 키워드 분석
        keyword_ranks = self.db.query(
            Keyword.term,
            func.count(DailyRank.id).label("appearances"),
            func.avg(DailyRank.rank).label("avg_rank"),
            func.min(DailyRank.rank).label("best_rank")
        ).join(DailyRank, DailyRank.keyword_id == Keyword.id)\
         .filter(
            and_(
                DailyRank.target_id == target_id,
                DailyRank.platform == platform,
                DailyRank.captured_at >= start_date
            )
        ).group_by(Keyword.term)\
         .order_by(func.count(DailyRank.id).desc())\
         .limit(20).all()

        top_keywords = [{
            "term": kr.term,
            "appearances": kr.appearances,
            "avg_rank": round(kr.avg_rank, 1),
            "best_rank": kr.best_rank
        } for kr in keyword_ranks]

        # 2. 시간대별 랭킹 패턴 분석 (광고 집행 패턴 추정)
        hourly_pattern = self.db.query(
            func.extract('hour', DailyRank.captured_at).label("hour"),
            func.count(DailyRank.id).label("count")
        ).filter(
            and_(
                DailyRank.target_id == target_id,
                DailyRank.platform == platform,
                DailyRank.captured_at >= start_date
            )
        ).group_by(func.extract('hour', DailyRank.captured_at)).all()

        activity_by_hour = {int(h.hour): h.count for h in hourly_pattern}

        # 3. 요일별 패턴 분석
        dow_pattern = self.db.query(
            func.extract('dow', DailyRank.captured_at).label("dow"),  # 0=Sunday, 6=Saturday
            func.count(DailyRank.id).label("count")
        ).filter(
            and_(
                DailyRank.target_id == target_id,
                DailyRank.platform == platform,
                DailyRank.captured_at >= start_date
            )
        ).group_by(func.extract('dow', DailyRank.captured_at)).all()

        dow_map = ["일", "월", "화", "수", "목", "금", "토"]
        activity_by_dow = {dow_map[int(d.dow)]: d.count for d in dow_pattern}

        # 4. 순위 트렌드 (최근 상승/하락 추세)
        recent_ranks = self.db.query(
            func.date(DailyRank.captured_at).label("date"),
            func.avg(DailyRank.rank).label("avg_rank")
        ).filter(
            and_(
                DailyRank.target_id == target_id,
                DailyRank.platform == platform,
                DailyRank.captured_at >= start_date
            )
        ).group_by(func.date(DailyRank.captured_at))\
         .order_by(func.date(DailyRank.captured_at).asc()).all()

        rank_trend = [{
            "date": str(r.date),
            "avg_rank": round(r.avg_rank, 1)
        } for r in recent_ranks]

        # 트렌드 방향 판단
        if len(rank_trend) >= 2:
            early_avg = sum(r["avg_rank"] for r in rank_trend[:len(rank_trend)//2]) / (len(rank_trend)//2)
            late_avg = sum(r["avg_rank"] for r in rank_trend[len(rank_trend)//2:]) / (len(rank_trend) - len(rank_trend)//2)
            trend_direction = "상승" if late_avg < early_avg else "하락" if late_avg > early_avg else "유지"
        else:
            trend_direction = "데이터 부족"

        return {
            "target_id": str(target_id),
            "target_name": target.name,
            "platform": platform.value,
            "analysis_period": f"{start_date} ~ {datetime.date.today()}",
            "top_keywords": top_keywords,
            "activity_by_hour": activity_by_hour,
            "activity_by_dow": activity_by_dow,
            "rank_trend": rank_trend,
            "trend_direction": trend_direction
        }

    def get_keyword_positioning_map(
        self,
        client_id: UUID,
        platform: PlatformType = PlatformType.NAVER_PLACE,
        days: int = 30
    ) -> Dict:
        """
        키워드 포지셔닝 맵 생성

        클라이언트와 주요 경쟁사들의 키워드별 순위를 시각화하기 위한 데이터 생성

        Returns:
            {
                "keywords": ["키워드1", "키워드2", ...],
                "targets": [
                    {"name": "우리 병원", "type": "OWNER", "ranks": [1, 3, 2, ...]},
                    {"name": "경쟁사A", "type": "COMPETITOR", "ranks": [2, 1, 4, ...]},
                    ...
                ]
            }
        """
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)

        # 1. 클라이언트 키워드 조회
        client_keywords = self.db.query(Keyword).filter(
            Keyword.client_id == client_id
        ).all()

        if not client_keywords:
            return {"keywords": [], "targets": []}

        keyword_ids = [kw.id for kw in client_keywords]
        keyword_map = {kw.id: kw.term for kw in client_keywords}

        # 2. 경쟁사 발굴 (상위 5개만)
        competitors = self.discover_competitors(
            client_id=client_id,
            platform=platform,
            keyword_overlap_threshold=0.2,
            top_n=5,
            days=days
        )

        competitor_ids = [UUID(c["target_id"]) for c in competitors]

        # 3. 각 키워드별, 각 타겟별 최신 순위 조회
        # 최신 snapshot 시간 찾기
        latest_time = self.db.query(func.max(DailyRank.captured_at)).filter(
            and_(
                DailyRank.keyword_id.in_(keyword_ids),
                DailyRank.platform == platform
            )
        ).scalar()

        if not latest_time:
            return {"keywords": [], "targets": []}

        # 최신 데이터 조회 (±5분 이내)
        time_window = datetime.timedelta(minutes=5)
        ranks = self.db.query(DailyRank).filter(
            and_(
                DailyRank.keyword_id.in_(keyword_ids),
                DailyRank.platform == platform,
                DailyRank.captured_at >= latest_time - time_window,
                DailyRank.captured_at <= latest_time + time_window
            )
        ).all()

        # 데이터 구조화: {target_id: {keyword_id: rank}}
        target_rank_map: Dict[UUID, Dict[UUID, int]] = defaultdict(dict)
        target_info_map: Dict[UUID, Target] = {}

        for rank in ranks:
            target_rank_map[rank.target_id][rank.keyword_id] = rank.rank
            if rank.target_id not in target_info_map:
                target_info_map[rank.target_id] = rank.target

        # 4. 포지셔닝 맵 데이터 생성
        targets_data = []

        # 경쟁사들만 포함
        for target_id in competitor_ids:
            if target_id in target_rank_map:
                target = target_info_map[target_id]
                ranks_list = [
                    target_rank_map[target_id].get(kw_id, None)
                    for kw_id in keyword_ids
                ]
                targets_data.append({
                    "id": str(target_id),
                    "name": target.name,
                    "type": target.type.value,
                    "ranks": ranks_list
                })

        return {
            "keywords": [keyword_map[kw_id] for kw_id in keyword_ids],
            "targets": targets_data,
            "snapshot_time": latest_time.isoformat() if latest_time else None
        }
