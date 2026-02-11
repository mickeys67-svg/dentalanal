from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from uuid import UUID
from app.core.database import get_db
from app.schemas.scraping import (
    SOVAnalysisRequest, SOVAnalysisResult, RankingRequest, RankingResultItem,
    CompetitorAnalysisRequest, CompetitorAnalysisResult,
    AIAnalysisRequest, AIAnalysisResponse
)
from app.schemas.analysis import EfficiencyReviewResponse
from app.services.analysis import AnalysisService
from app.services.ai_service import AIService
from app.services.benchmark_service import BenchmarkService
from app.models.models import PlatformType, User
from app.api.endpoints.auth import get_current_user

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
             raise HTTPException(status_code=400, detail=report)
        return AIAnalysisResponse(report=report)
    except HTTPException:
        raise
    except Exception as e:
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
    return results

@router.get("/ranking-trend")
def get_ranking_trend(
    keyword: str,
    target_hospital: str,
    platform: str = "NAVER_PLACE",
    days: int = 30,
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    p_type = PlatformType.NAVER_VIEW if platform == "NAVER_VIEW" else PlatformType.NAVER_PLACE
    return service.get_ranking_trend(keyword, target_hospital, p_type, days)

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

@router.get("/funnel/{client_id}")
def get_funnel_analysis(client_id: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.get_funnel_data(client_id)

@router.get("/cohort/{client_id}")
def get_cohort_analysis(client_id: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.get_cohort_data(client_id)

@router.get("/attribution/{client_id}")
def get_attribution_analysis(client_id: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.calculate_attribution(client_id)

@router.get("/segments/{client_id}")
def get_segment_analysis(client_id: str, db: Session = Depends(get_db)):
    service = AnalysisService(db)
    return service.get_segment_analysis(client_id)

@router.get("/weekly-summary")
def get_weekly_summary(
    target_hospital: str,
    keywords: str, # Comma separated list
    platform: str = "NAVER_PLACE",
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    kw_list = [k.strip() for k in keywords.split(",")]
    p_type = PlatformType.NAVER_VIEW if platform == "NAVER_VIEW" else PlatformType.NAVER_PLACE
    return service.get_weekly_sov_summary(target_hospital, kw_list, p_type)
def get_current_user_wrapper(db: Session = Depends(get_db), token: str = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/login"))):
    from app.api.endpoints.auth import get_current_user
    return get_current_user(token, db)

@router.get("/benchmark/{client_id}")
def get_benchmark_comparison(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_wrapper)
):
    service = BenchmarkService(db)
    return service.compare_client_performance(client_id)

@router.get("/efficiency/{client_id}", response_model=EfficiencyReviewResponse)
def get_efficiency_review(
    client_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    ai_service = AIService()
    
    # 1. Get raw efficiency data
    data = service.get_efficiency_data(str(client_id), days)
    
    # 2. Generate AI review (structured)
    if data["items"]:
        ai_res = ai_service.generate_efficiency_review(data)
        data["ai_review"] = ai_res.get("overall", "분석 결과를 불러오는 중입니다.")
        
        # Map suggestions back to items
        suggestions = ai_res.get("suggestions", {})
        for item in data["items"]:
            item_name = item["name"]
            if item_name in suggestions:
                item["suggestion"] = suggestions[item_name]
    else:
        data["ai_review"] = "분석할 수 있는 광고 집행 데이터가 충분하지 않습니다."
        
    return data
