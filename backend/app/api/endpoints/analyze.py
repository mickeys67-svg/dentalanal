from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.scraping import (
    SOVAnalysisRequest, SOVAnalysisResult, RankingRequest, RankingResultItem,
    CompetitorAnalysisRequest, CompetitorAnalysisResult,
    AIAnalysisRequest, AIAnalysisResponse
)
from app.services.analysis import AnalysisService
from app.services.ai_service import AIService
from app.models.models import PlatformType

router = APIRouter()

@router.post("/ai-report", response_model=AIAnalysisResponse)
def get_ai_report(
    request: AIAnalysisRequest,
    db: Session = Depends(get_db)
):
    analysis_service = AnalysisService(db)
    ai_service = AIService()
    
    platform = PlatformType.NAVER_VIEW if request.platform == "NAVER_VIEW" else PlatformType.NAVER_PLACE
    
    # 1. Get SOV
    sov_data = analysis_service.calculate_sov(request.keyword, request.target_hospital, platform, request.top_n)
    
    # 2. Get Competitors
    comp_data = analysis_service.get_competitor_analysis(request.keyword, platform, request.top_n)
    
    # 3. Generate AI Report
    try:
        report = ai_service.generate_marketing_report(
            request.keyword, 
            sov_data["sov"], 
            comp_data["competitors"]
        )
        if "API 키가 설정되지 않았습니다" in report:
             from fastapi import HTTPException
             raise HTTPException(status_code=400, detail=report)
        return AIAnalysisResponse(report=report)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Gemini 서비스 오류: {str(e)}")

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
        # Check specific platform requested
        platform = PlatformType.NAVER_VIEW if request.platform == "NAVER_VIEW" else PlatformType.NAVER_PLACE
        
        sov_data = service.calculate_sov(keyword, request.target_hospital, platform, request.top_n)
        
        results.append(SOVAnalysisResult(
            keyword=keyword,
            total_items=sov_data["total"],
            target_hits=sov_data["hits"],
            sov_score=sov_data["sov"],
            top_rank=sov_data.get("top_rank") # Assuming service might return this
        ))
        
    return results
