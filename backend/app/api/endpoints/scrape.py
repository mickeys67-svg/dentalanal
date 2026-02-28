from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.schemas.scraping import ScrapeRequest, ScrapeResponse
from app.worker.tasks import scrape_place_task, scrape_view_task, scrape_ad_task
from app.api.endpoints.auth import get_current_user
from app.models.models import User, DailyRank, Keyword, Target, PlatformType
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# 동시 스크래핑 방지 추적 (메모리, 재시작 시 초기화)
# Format: {"{client_id}:{platform}:{keyword}": task_id}
_active_scraping_tasks: dict = {}

PLATFORM_ENUM_MAP = {
    "NAVER_PLACE": PlatformType.NAVER_PLACE,
    "NAVER_VIEW": PlatformType.NAVER_VIEW,
    "NAVER_AD": PlatformType.NAVER_AD,
}


def _make_task_key(client_id: str, platform: str, keyword: str) -> str:
    return f"{client_id}:{platform}:{keyword}"


@router.post("/place", response_model=ScrapeResponse)
async def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_key = _make_task_key(request.client_id, "naver_place", request.keyword)
    if task_key in _active_scraping_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"네이버 플레이스 '{request.keyword}' 조사가 이미 진행 중입니다.",
        )

    task_id = str(uuid.uuid4())
    _active_scraping_tasks[task_key] = task_id

    async def _run_and_cleanup():
        try:
            await scrape_place_task(request.keyword, request.client_id)
        finally:
            _active_scraping_tasks.pop(task_key, None)

    background_tasks.add_task(_run_and_cleanup)

    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 플레이스 조사({request.keyword})가 시작되었습니다.",
    )


@router.post("/view", response_model=ScrapeResponse)
async def trigger_view_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_key = _make_task_key(request.client_id, "naver_view", request.keyword)
    if task_key in _active_scraping_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"네이버 VIEW '{request.keyword}' 조사가 이미 진행 중입니다.",
        )

    task_id = str(uuid.uuid4())
    _active_scraping_tasks[task_key] = task_id

    async def _run_and_cleanup():
        try:
            await scrape_view_task(request.keyword, request.client_id)
        finally:
            _active_scraping_tasks.pop(task_key, None)

    background_tasks.add_task(_run_and_cleanup)

    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 VIEW 조사({request.keyword})가 시작되었습니다.",
    )


@router.post("/ad", response_model=ScrapeResponse)
async def trigger_ad_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task_key = _make_task_key(request.client_id, "naver_ad", request.keyword)
    if task_key in _active_scraping_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"네이버 광고 '{request.keyword}' 조사가 이미 진행 중입니다.",
        )

    task_id = str(uuid.uuid4())
    _active_scraping_tasks[task_key] = task_id

    async def _run_and_cleanup():
        try:
            await scrape_ad_task(request.keyword, request.client_id)
        finally:
            _active_scraping_tasks.pop(task_key, None)

    background_tasks.add_task(_run_and_cleanup)

    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 광고 조사({request.keyword})가 시작되었습니다.",
    )


@router.get("/results")
def get_scrape_results(
    client_id: str = Query(..., description="Client ID"),
    keyword: str = Query(..., description="검색 키워드"),
    platform: str = Query("NAVER_PLACE", description="NAVER_PLACE | NAVER_VIEW | NAVER_AD"),
    hours: int = Query(24, description="최근 N시간 데이터"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    스크래핑 결과 조회.
    - client_id 파라미터로 키워드 검색 (버그 수정)
    - target_type을 target.type 직접 참조로 수정 (AttributeError 수정)
    """
    try:
        # [BUG FIX 1] 요청의 client_id 파라미터를 실제로 사용 (기존: current_user.id로 잘못 참조)
        keyword_obj = db.query(Keyword).filter(
            Keyword.client_id == client_id,
            Keyword.term == keyword,
        ).first()

        # client_id로 못 찾으면 현재 유저 소속 에이전시에서도 탐색
        if not keyword_obj and current_user.agency_id:
            from app.models.models import Client
            agency_client_ids = [
                c.id for c in db.query(Client).filter(
                    Client.agency_id == current_user.agency_id
                ).all()
            ]
            keyword_obj = db.query(Keyword).filter(
                Keyword.client_id.in_(agency_client_ids),
                Keyword.term == keyword,
            ).first()

        if not keyword_obj:
            return {
                "has_data": False,
                "keyword": keyword,
                "platform": platform,
                "results": [],
                "total_count": 0,
                "message": "키워드 레코드를 찾을 수 없습니다. 먼저 스크래핑을 실행하세요.",
            }

        platform_enum = PLATFORM_ENUM_MAP.get(platform.upper(), PlatformType.NAVER_PLACE)
        since = datetime.utcnow() - timedelta(hours=hours)

        daily_ranks = (
            db.query(DailyRank)
            .filter(
                DailyRank.keyword_id == keyword_obj.id,
                DailyRank.platform == platform_enum,
                DailyRank.captured_at >= since,
            )
            .order_by(desc(DailyRank.captured_at))
            .all()
        )

        if not daily_ranks:
            return {
                "has_data": False,
                "keyword": keyword,
                "platform": platform,
                "results": [],
                "total_count": 0,
                "message": f"최근 {hours}시간 내 데이터 없음. 스크래핑 실행 후 잠시 기다려주세요.",
            }

        # 타겟별 최신 순위만 유지
        seen_targets: dict = {}
        for rank_record in daily_ranks:
            if rank_record.target_id in seen_targets:
                continue

            target = db.query(Target).filter(Target.id == rank_record.target_id).first()
            if not target:
                continue

            # [BUG FIX 2] rank_record.client.targets.filter_by() 제거 → target.type 직접 참조
            seen_targets[rank_record.target_id] = {
                "target_id": str(target.id),
                "target_name": target.name,
                "target_type": target.type.value if target.type else "OTHERS",
                "rank": rank_record.rank,
                "rank_change": rank_record.rank_change or 0,
                "captured_at": (
                    rank_record.captured_at.isoformat()
                    if rank_record.captured_at
                    else None
                ),
            }

        results = list(seen_targets.values())
        # 순위 오름차순 정렬
        results.sort(key=lambda x: x["rank"])

        return {
            "has_data": len(results) > 0,
            "keyword": keyword,
            "platform": platform,
            "results": results,
            "total_count": len(results),
            "message": f"{len(results)}개 타겟 데이터",
        }

    except Exception as e:
        import traceback
        logger.error(f"get_scrape_results 오류: {e}\n{traceback.format_exc()}")
        return {
            "has_data": False,
            "keyword": keyword,
            "platform": platform,
            "results": [],
            "total_count": 0,
            "message": f"서버 오류: {str(e)}",
        }


@router.get("/status")
def get_scraping_status():
    """현재 진행 중인 스크래핑 작업 목록"""
    return {
        "active_tasks": len(_active_scraping_tasks),
        "tasks": list(_active_scraping_tasks.keys()),
    }
