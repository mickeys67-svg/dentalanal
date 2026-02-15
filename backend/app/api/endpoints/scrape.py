from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.scraping import ScrapeRequest, ScrapeResponse
from app.worker.tasks import scrape_place_task, scrape_view_task
import uuid

router = APIRouter()

@router.post("/place", response_model=ScrapeResponse)
def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    # Offload to BackgroundTasks ( Celery delay is mocked out/unstable in this env )
    background_tasks.add_task(scrape_place_task, request.keyword)
    
    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 플레이스 조사({request.keyword})가 백그라운드에서 시작되었습니다."
    )

@router.post("/view", response_model=ScrapeResponse)
def trigger_view_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    # Offload to BackgroundTasks
    background_tasks.add_task(scrape_view_task, request.keyword)
    
    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 VIEW 조사({request.keyword})가 백그라운드에서 시작되었습니다."
    )

@router.post("/ad", response_model=ScrapeResponse)
def trigger_ad_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    from app.worker.tasks import scrape_ad_task
    # Offload to BackgroundTasks
    background_tasks.add_task(scrape_ad_task, request.keyword)
    
    return ScrapeResponse(
        task_id=task_id,
        message=f"네이버 광고 조사({request.keyword})가 백그라운드에서 시작되었습니다."
    )
