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
    # Offload to Celery
    task = scrape_place_task.delay(request.keyword)
    
    return ScrapeResponse(
        task_id=task.id,
        message=f"Started scraping Place for keyword: {request.keyword}"
    )

@router.post("/view", response_model=ScrapeResponse)
def trigger_view_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    # Offload to Celery
    task = scrape_view_task.delay(request.keyword)
    
    return ScrapeResponse(
        task_id=task.id,
        message=f"Started scraping View for keyword: {request.keyword}"
    )
