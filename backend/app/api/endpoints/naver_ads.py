from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import DailyRank, Keyword, PlatformType, Target
from datetime import datetime, timedelta
from sqlalchemy import desc
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/naver", tags=["Naver Ads"])


@router.get("/collected-data")
def get_collected_naver_data(
    client_id: str = Query(..., description="클라이언트 ID"),
    days: int = Query(30, description="조회 기간 (일)"),
    db: Session = Depends(get_db)
):
    """
    수집된 Naver 데이터 조회

    테스트용: 실제로 DB에 뭐가 들어왔는지 확인
    - NAVER_PLACE (플레이스 순위)
    - NAVER_VIEW (블로그 순위)
    - NAVER_AD (광고 성과) - 추후 추가

    응답:
    - status: SUCCESS / NO_DATA / NO_RANKS
    - summary: 통계 정보
    - keywords: 키워드 목록
    - ranks: 수집된 순위 데이터 목록
    """
    try:
        logger.info(f"📊 Naver 데이터 조회 시작: client_id={client_id}, days={days}")

        # 1. 해당 클라이언트의 키워드 조회
        keywords = db.query(Keyword).filter(
            Keyword.client_id == client_id
        ).all()

        logger.info(f"   ✓ 키워드 {len(keywords)}개 조회됨")

        if not keywords:
            return {
                "status": "NO_DATA",
                "message": "해당 클라이언트의 키워드가 없습니다",
                "keywords": [],
                "ranks": []
            }

        keyword_ids = [k.id for k in keywords]

        # 2. 최근 days일의 Naver 데이터 조회
        since = datetime.utcnow() - timedelta(days=days)
        ranks = db.query(DailyRank).filter(
            DailyRank.keyword_id.in_(keyword_ids),
            DailyRank.platform.in_([
                PlatformType.NAVER_PLACE,
                PlatformType.NAVER_VIEW
            ]),
            DailyRank.captured_at >= since
        ).order_by(desc(DailyRank.captured_at)).all()

        logger.info(f"   ✓ 순위 데이터 {len(ranks)}개 조회됨")

        if not ranks:
            return {
                "status": "NO_RANKS",
                "message": f"최근 {days}일간 수집된 순위 데이터가 없습니다",
                "keywords": [
                    {
                        "id": str(k.id),
                        "term": k.term,
                        "category": k.category
                    }
                    for k in keywords
                ],
                "ranks": []
            }

        # 3. 데이터 정리
        rank_data = [
            {
                "id": str(r.id),
                "keyword": r.keyword.term,
                "target": r.target.name,
                "target_type": r.target.type.value,
                "platform": r.platform.value,
                "rank": r.rank,
                "rank_change": r.rank_change,
                "captured_at": r.captured_at.isoformat(),
                "captured_date": r.captured_at.strftime("%Y-%m-%d")
            }
            for r in ranks
        ]

        # 4. 통계 계산
        unique_dates = sorted(set(r.captured_at.date() for r in ranks))
        unique_keywords = set(r.keyword.term for r in ranks)
        unique_targets = set(r.target.name for r in ranks)
        platforms = set(r.platform.value for r in ranks)

        total_records = len(ranks)

        # 5. 플랫폼별 통계
        platform_stats = {}
        for platform in platforms:
            platform_count = len([r for r in ranks if r.platform.value == platform])
            platform_stats[platform] = platform_count

        # 6. 키워드별 순위 범위
        keyword_rank_ranges = {}
        for kw_id in keyword_ids:
            kw_ranks = [r.rank for r in ranks if r.keyword_id == kw_id]
            if kw_ranks:
                kw = next(k for k in keywords if k.id == kw_id)
                keyword_rank_ranges[kw.term] = {
                    "min_rank": min(kw_ranks),
                    "max_rank": max(kw_ranks),
                    "avg_rank": round(sum(kw_ranks) / len(kw_ranks), 2),
                    "record_count": len(kw_ranks)
                }

        logger.info(f"   ✓ 데이터 처리 완료")

        return {
            "status": "SUCCESS",
            "message": f"총 {total_records}개의 순위 데이터 발견",
            "summary": {
                "total_records": total_records,
                "unique_dates": len(unique_dates),
                "date_range": {
                    "start": min(unique_dates).isoformat() if unique_dates else None,
                    "end": max(unique_dates).isoformat() if unique_dates else None,
                    "days": len(unique_dates)
                },
                "keywords_count": len(unique_keywords),
                "targets_count": len(unique_targets),
                "platforms": platform_stats
            },
            "keywords": [
                {
                    "id": str(k.id),
                    "term": k.term,
                    "category": k.category,
                    "rank_info": keyword_rank_ranges.get(k.term, None)
                }
                for k in keywords
            ],
            "rank_data": {
                "total": total_records,
                "by_platform": platform_stats,
                "by_keyword": keyword_rank_ranges,
                "records": rank_data
            }
        }

    except Exception as e:
        logger.error(f"❌ Naver 데이터 조회 실패: {str(e)}", exc_info=True)
        return {
            "status": "ERROR",
            "message": str(e),
            "keywords": [],
            "ranks": []
        }


@router.get("/summary")
def get_naver_summary(
    client_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Naver 광고 데이터 요약 (간단 버전)

    최근 데이터만 빠르게 확인
    """
    try:
        # 최근 1일 데이터
        since = datetime.utcnow() - timedelta(days=1)

        keywords = db.query(Keyword).filter(
            Keyword.client_id == client_id
        ).all()

        if not keywords:
            return {"status": "NO_DATA", "message": "키워드 없음"}

        keyword_ids = [k.id for k in keywords]

        ranks = db.query(DailyRank).filter(
            DailyRank.keyword_id.in_(keyword_ids),
            DailyRank.platform.in_([PlatformType.NAVER_PLACE, PlatformType.NAVER_VIEW]),
            DailyRank.captured_at >= since
        ).all()

        # 요약 데이터
        summary = {}
        for keyword in keywords:
            kw_ranks = [r for r in ranks if r.keyword_id == keyword.id]
            summary[keyword.term] = {
                "records": len(kw_ranks),
                "avg_rank": round(sum(r.rank for r in kw_ranks) / len(kw_ranks), 2) if kw_ranks else 0,
                "latest": kw_ranks[0].rank if kw_ranks else None
            }

        return {
            "status": "SUCCESS",
            "message": f"최근 데이터 {len(ranks)}개",
            "summary": summary
        }

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


@router.get("/rank-history")
def get_rank_history(
    client_id: str = Query(...),
    keyword: str = Query(..., description="조회할 키워드"),
    days: int = Query(7),
    db: Session = Depends(get_db)
):
    """
    특정 키워드의 순위 변화 조회

    예: /api/v1/naver/rank-history?client_id=xxx&keyword=임플란트&days=7
    """
    try:
        # 키워드 찾기
        kw_obj = db.query(Keyword).filter(
            Keyword.client_id == client_id,
            Keyword.term == keyword
        ).first()

        if not kw_obj:
            return {
                "status": "NOT_FOUND",
                "message": f"키워드 '{keyword}'를 찾을 수 없습니다"
            }

        # 순위 데이터 조회
        since = datetime.utcnow() - timedelta(days=days)
        ranks = db.query(DailyRank).filter(
            DailyRank.keyword_id == kw_obj.id,
            DailyRank.platform.in_([PlatformType.NAVER_PLACE, PlatformType.NAVER_VIEW]),
            DailyRank.captured_at >= since
        ).order_by(DailyRank.captured_at).all()

        if not ranks:
            return {
                "status": "NO_DATA",
                "message": f"'{keyword}'의 데이터가 없습니다",
                "keyword": keyword
            }

        # 데이터 정리 (날짜별)
        history_by_date = {}
        for rank in ranks:
            date_str = rank.captured_at.strftime("%Y-%m-%d")
            if date_str not in history_by_date:
                history_by_date[date_str] = []

            history_by_date[date_str].append({
                "target": rank.target.name,
                "rank": rank.rank,
                "rank_change": rank.rank_change,
                "platform": rank.platform.value,
                "time": rank.captured_at.strftime("%H:%M:%S")
            })

        return {
            "status": "SUCCESS",
            "keyword": keyword,
            "days": days,
            "total_records": len(ranks),
            "date_range": {
                "start": min(r.captured_at for r in ranks).isoformat(),
                "end": max(r.captured_at for r in ranks).isoformat()
            },
            "history": history_by_date
        }

    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
