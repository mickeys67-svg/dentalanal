from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.scraping import (
    SOVAnalysisRequest, SOVAnalysisResult, RankingRequest, RankingResultItem,
    CompetitorAnalysisRequest, CompetitorAnalysisResult
)
from app.services.analysis import AnalysisService
from app.models.models import PlatformType

router = APIRouter()

@router.post("/competitors", response_model=CompetitorAnalysisResult)
def analyze_competitors(
    request: CompetitorAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    platform = PlatformType.NAVER_VIEW if request.platform == "NAVER_VIEW" else PlatformType.NAVER_PLACE
    return service.get_competitor_analysis(request.keyword, platform, request.top_n)

@router.post("/rankings", response_model=List[RankingResultItem])
def get_rankings(
    request: RankingRequest,
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    
    platform = PlatformType.NAVER_PLACE
    if request.platform == "NAVER_VIEW":
        platform = PlatformType.NAVER_VIEW
        
    results = service.get_daily_ranks(request.keyword, platform)
    
    # Map to schema
    # Logic in service returns dict, schema expects matching fields
    return results

@router.post("/sov", response_model=List[SOVAnalysisResult])
def analyze_sov(
    request: SOVAnalysisRequest,
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    results = []
    
    for keyword in request.keywords:
        # Check both Place and View
        # Here we just return Place SOV for simplicity or aggregate
        # Let's return separate items per keyword/platform if needed, 
        # or just specific platform requested. 
        # For now, let's just return View SOV as an example or avg.
        # Impl: Return View SOV (Blog)
        
        sov_data = service.calculate_sov(keyword, request.target_hospital, PlatformType.NAVER_VIEW, request.top_n)
        
        results.append(SOVAnalysisResult(
            keyword=keyword,
            total_items=sov_data["total"],
            target_hits=sov_data["hits"],
            sov_score=sov_data["sov"]
        ))
        
    return results
