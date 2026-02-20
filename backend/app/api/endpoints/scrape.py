from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.schemas.scraping import ScrapeRequest, ScrapeResponse
from app.worker.tasks import scrape_place_task, scrape_view_task
from app.api.endpoints.auth import get_current_user
from app.models.models import User, DailyRank, Keyword, Target, PlatformType
from datetime import datetime, timedelta
import uuid

router = APIRouter()

# Global tracking of active scraping tasks (prevent concurrent requests)
# Format: {f"{client_id}:{keyword}:{platform}": task_id}
_active_scraping_tasks = {}

@router.post("/place", response_model=ScrapeResponse)
def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check for concurrent scraping on the same parameters
    task_key = f"{request.client_id}:naver_place:{request.keyword}"
    if task_key in _active_scraping_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"네이버 플레이스 '{request.keyword}' 조사가 이미 진행 중입니다. 완료될 때까지 기다려주세요."
        )

    task_id = str(uuid.uuid4())
    _active_scraping_tasks[task_key] = task_id

    def cleanup_task():
        """Cleanup function to remove task from tracking after completion"""
        _active_scraping_tasks.pop(task_key, None)

    # Offload to BackgroundTasks ( Celery delay is mocked out/unstable in this env )
    background_tasks.add_task(scrape_place_task, request.keyword, request.client_id)
    background_tasks.add_task(cleanup_task)

    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 플레이스 조사({request.keyword})가 백그라운드에서 시작되었습니다."
    )

@router.post("/view", response_model=ScrapeResponse)
def trigger_view_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check for concurrent scraping on the same parameters
    task_key = f"{request.client_id}:naver_view:{request.keyword}"
    if task_key in _active_scraping_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"네이버 VIEW '{request.keyword}' 조사가 이미 진행 중입니다. 완료될 때까지 기다려주세요."
        )

    task_id = str(uuid.uuid4())
    _active_scraping_tasks[task_key] = task_id

    def cleanup_task():
        """Cleanup function to remove task from tracking after completion"""
        _active_scraping_tasks.pop(task_key, None)

    # Offload to BackgroundTasks
    background_tasks.add_task(scrape_view_task, request.keyword, request.client_id)
    background_tasks.add_task(cleanup_task)

    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 VIEW 조사({request.keyword})가 백그라운드에서 시작되었습니다."
    )

@router.post("/ad", response_model=ScrapeResponse)
def trigger_ad_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check for concurrent scraping on the same parameters
    task_key = f"{request.client_id}:naver_ad:{request.keyword}"
    if task_key in _active_scraping_tasks:
        raise HTTPException(
            status_code=409,
            detail=f"네이버 광고 '{request.keyword}' 조사가 이미 진행 중입니다. 완료될 때까지 기다려주세요."
        )

    task_id = str(uuid.uuid4())
    _active_scraping_tasks[task_key] = task_id

    def cleanup_task():
        """Cleanup function to remove task from tracking after completion"""
        _active_scraping_tasks.pop(task_key, None)

    from app.worker.tasks import scrape_ad_task
    # Offload to BackgroundTasks
    background_tasks.add_task(scrape_ad_task, request.keyword, request.client_id)
    background_tasks.add_task(cleanup_task)

    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 광고 조사({request.keyword})가 백그라운드에서 시작되었습니다."
    )

@router.get("/results")
def get_scrape_results(
    client_id: str = Query(..., description="Client ID"),
    keyword: str = Query(..., description="Keyword to search for"),
    platform: str = Query("NAVER_PLACE", description="Platform: NAVER_PLACE, NAVER_VIEW, NAVER_AD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch scraping results for a given client, keyword, and platform.
    Returns the most recent ranking data from the last 24 hours.
    """
    try:
        # Find keyword by client_id and term
        keyword_obj = db.query(Keyword).filter(
            Keyword.client_id == current_user.agency_id if current_user.role.value == 'AGENCY' else current_user.id,
            Keyword.term == keyword
        ).first()

        if not keyword_obj:
            return {
                "has_data": False,
                "keyword": keyword,
                "platform": platform,
                "results": [],
                "total_count": 0,
                "message": "No keyword record found"
            }

        # Map platform string to enum
        platform_enum_map = {
            "NAVER_PLACE": PlatformType.NAVER_PLACE,
            "NAVER_VIEW": PlatformType.NAVER_VIEW,
            "NAVER_AD": PlatformType.NAVER_AD
        }

        platform_enum = platform_enum_map.get(platform, PlatformType.NAVER_PLACE)

        # Query recent ranks for this keyword and platform (last 24 hours)
        since = datetime.utcnow() - timedelta(hours=24)

        daily_ranks = db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword_obj.id,
            DailyRank.platform == platform_enum,
            DailyRank.captured_at >= since
        ).order_by(desc(DailyRank.captured_at)).all()

        if not daily_ranks:
            return {
                "has_data": False,
                "keyword": keyword,
                "platform": platform,
                "results": [],
                "total_count": 0,
                "message": "No ranking data found yet"
            }

        # Group by target and get the latest rank for each
        target_ranks = {}
        for rank_record in daily_ranks:
            target = db.query(Target).filter(Target.id == rank_record.target_id).first()
            if target and target.id not in target_ranks:
                target_ranks[target.id] = {
                    "target_id": str(target.id),
                    "target_name": target.name,
                    "target_type": str(rank_record.client.targets.filter_by(id=rank_record.target_id).first().type) if rank_record.client else "UNKNOWN",
                    "rank": rank_record.rank,
                    "rank_change": rank_record.rank_change or 0,
                    "captured_at": rank_record.captured_at.isoformat() if rank_record.captured_at else None
                }

        results = list(target_ranks.values())

        return {
            "has_data": len(results) > 0,
            "keyword": keyword,
            "platform": platform,
            "results": results,
            "total_count": len(results),
            "message": f"Found {len(results)} targets"
        }

    except Exception as e:
        import logging
        logging.error(f"Error fetching scrape results: {str(e)}")
        return {
            "has_data": False,
            "keyword": keyword,
            "platform": platform,
            "results": [],
            "total_count": 0,
            "message": f"Error: {str(e)}"
        }
