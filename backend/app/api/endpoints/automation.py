from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.services.ai_service import AIService
from app.core.database import get_db
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter()
ai_service = AIService()

class AdCopyRequest(BaseModel):
    swot_data: Dict
    target_audience: str
    key_proposition: str

class RecommendationRequest(BaseModel):
    campaigns: List[Dict]

@router.post("/generate-copy")
def generate_copy(data: AdCopyRequest):
    """
    Generate AI ad copy based on SWOT and target info.
    """
    result = ai_service.generate_ad_copy(
        data.swot_data, 
        data.target_audience, 
        data.key_proposition
    )
    return result

@router.post("/recommendations")
def get_recommendations(data: RecommendationRequest):
    """
    Get AI-driven campaign optimization recommendations.
    """
    result = ai_service.analyze_performance_optimization(data.campaigns)
    return result

@router.post("/sync")
def trigger_full_sync(background_tasks: BackgroundTasks):
    """
    Trigger full-channel data synchronization.
    """
    from app.scripts.sync_data import sync_all_channels
    background_tasks.add_task(sync_all_channels)
    return {"status": "SUCCESS", "message": "전체 채널 데이터 동기화가 시작되었습니다."}
