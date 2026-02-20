from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
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
from app.models.models import PlatformType, User, DailyRank, Target, Keyword, TargetType, Client
from app.api.endpoints.auth import get_current_user
from fastapi.responses import StreamingResponse
import io
import json
import csv
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import List, Union, Optional, Dict

router = APIRouter()

@router.post("/ai-report", response_model=AIAnalysisResponse)
def get_ai_report(
    request: AIAnalysisRequest,
    background_tasks: BackgroundTasks,
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
def get_funnel_analysis(
    client_id: str, 
    days: int = 30, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    
    # Parse dates if provided
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
    
    return service.get_funnel_data(client_id, start_date=s_date, end_date=e_date, days=days)

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
    client_id: str,
    background_tasks: BackgroundTasks,
    days: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Handle "undefined" or other invalid strings
    if client_id == "undefined" or client_id == "null":
        return {
            "items": [],
            "overall_roas": 0.0,
            "total_spend": 0,
            "total_conversions": 0,
            "period": "데이터를 불러올 수 없습니다 (선택된 업체 없음)",
            "ai_review": "분석할 수 있는 광고 집행 데이터가 충분하지 않습니다."
        }
    
    try:
        validated_id = str(UUID(client_id))
    except (ValueError, TypeError):
         raise HTTPException(status_code=400, detail="Invalid client_id format")

    service = AnalysisService(db)
    ai_service = AIService()
    
    # Parse dates if provided
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    # 1. Get raw efficiency data
    data = service.get_efficiency_data(validated_id, start_date=s_date, end_date=e_date, days=days)
    
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

# --- Market Analysis Endpoints (Phase 3) ---

@router.get("/market/landscape")
def get_market_landscape(
    keyword: str,
    platform: str = "NAVER_PLACE",
    top_n: int = 10,
    db: Session = Depends(get_db)
):
    from app.services.competitor_service import CompetitorService
    service = CompetitorService(db)
    p_type = PlatformType.NAVER_VIEW if platform == "NAVER_VIEW" else PlatformType.NAVER_PLACE
    return service.get_competitor_landscape(keyword, p_type, top_n)

@router.get("/market/spend")
def estimate_competitor_spend(
    keywords: str, # Comma separated
    db: Session = Depends(get_db)
):
    from app.services.competitor_service import CompetitorService
    service = CompetitorService(db)
    kw_list = [k.strip() for k in keywords.split(",")]
    return service.estimate_ad_spend(kw_list)

@router.get("/market/reputation")
def compare_market_reputation(
    hospitals: str, # Comma separated
    db: Session = Depends(get_db)
):
    from app.services.competitor_service import CompetitorService
    service = CompetitorService(db)
    h_list = [h.strip() for h in hospitals.split(",")]
    return service.get_reputation_comparison(h_list)

# --- Onboarding Wizard Schemas ---

class TargetItem(BaseModel):
    name: str
    target_type: TargetType
    url: Optional[str] = None

class BulkTargetRequest(BaseModel):
    client_id: UUID
    targets: List[TargetItem]

@router.post("/targets/bulk")
def bulk_update_targets(
    request: BulkTargetRequest,
    db: Session = Depends(get_db)
):
    """
    Bulk register/update owner and competitor targets for a specific client.
    """
    client = db.query(Client).filter(Client.id == request.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    results = []
    for item in request.targets:
        target = db.query(Target).filter(Target.name == item.name).first()
        if not target:
            target = Target(
                id=uuid4(),
                name=item.name,
                type=item.target_type,
                urls={"default": item.url} if item.url else None
            )
            db.add(target)
            db.flush()
        else:
            # Update existing target type/url if needed
            target.type = item.target_type
            if item.url:
                target.urls = {"default": item.url}
        
        results.append({"id": str(target.id), "name": target.name})
    
    db.commit()
    return {"status": "SUCCESS", "targets": results}

@router.get("/targets/search")
def search_targets(
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search existing targets by name or return recent ones."""
    query = db.query(Target)
    if name:
        return query.filter(Target.name.ilike(f"%{name}%")).limit(10).all()
    # If no name provided, return 10 most recently created/used targets
    return query.order_by(Target.id.desc()).limit(10).all()

class HistoryCreate(BaseModel):
    client_id: UUID
    keyword: str
    platform: str
    result_data: Optional[Dict] = None
    is_saved: bool = False

@router.post("/history")
def save_analysis_history(
    request: HistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save record of analysis execution, potentially with results."""
    from app.models.models import AnalysisHistory
    history = AnalysisHistory(
        id=uuid4(),
        client_id=request.client_id,
        keyword=request.keyword,
        platform=request.platform,
        result_data=request.result_data,
        is_saved=request.is_saved
    )
    db.add(history)
    db.commit()
    return {"status": "SUCCESS", "id": str(history.id)}

@router.put("/history/{history_id}/save")
def finalize_and_save_history(
    history_id: UUID,
    result_data: Dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually finalize and save the investigation results."""
    from app.models.models import AnalysisHistory
    history = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not history:
        raise HTTPException(status_code=404, detail="조사 기록을 찾을 수 없습니다.")
    
    history.result_data = result_data
    history.is_saved = True
    db.commit()
    return {"status": "SUCCESS", "message": "결과가 성공적으로 저장되었습니다."}

@router.get("/history/{history_id}/download")
def download_analysis_result(
    history_id: UUID,
    format: str = "json", # json or csv
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the saved analysis result."""
    from app.models.models import AnalysisHistory
    history = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if not history or not history.result_data:
        raise HTTPException(status_code=404, detail="저장된 결과 데이터가 없습니다.")

    filename = f"analysis_{history.keyword}_{history.created_at.strftime('%Y%m%d')}"
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        # Assuming result_data is a dict, we flatten it a bit or just dump as rows
        writer.writerow(["Field", "Value"])
        for k, v in history.result_data.items():
            writer.writerow([k, str(v)])
        
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    
    # Default to JSON
    return StreamingResponse(
        io.BytesIO(json.dumps(history.result_data, indent=2, ensure_ascii=False).encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}.json"}
    )

@router.get("/history/{client_id}")
def get_analysis_history(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent 10 analysis histories for a client."""
    from app.models.models import AnalysisHistory
    return db.query(AnalysisHistory).filter(
        AnalysisHistory.client_id == client_id
    ).order_by(AnalysisHistory.created_at.desc()).limit(10).all()


# --- AI Assistant Endpoints (Phase 6) ---

class SWOTRequest(BaseModel):
    hospital_name: str
    competitor_info: List[Dict] = []

class BenchmarkDiagnosisRequest(BaseModel):
    client_id: str

class AssistantQueryRequest(BaseModel):
    query: str
    client_id: Optional[str] = None

QUICK_QUERIES = [
    {"id": "status", "label": "지금 성과 어때?", "description": "효율성 리뷰 기반 현황 진단"},
    {"id": "advice", "label": "개선 포인트 알려줘", "description": "캠페인 최적화 제안"},
    {"id": "top_keyword", "label": "상위 키워드는?", "description": "노출 점유율 상위 키워드"},
    {"id": "budget", "label": "다음 달 예산은?", "description": "예산 재분배 추천"},
    {"id": "swot", "label": "SWOT 분석", "description": "강점/약점/기회/위협 분석"},
]

@router.get("/assistant/quick-queries")
def get_quick_queries():
    """사전 정의된 AI 빠른 질문 목록 반환"""
    return QUICK_QUERIES

@router.post("/assistant/swot")
def generate_swot(
    request: SWOTRequest,
    db: Session = Depends(get_db)
):
    """SWOT 분석 생성"""
    ai_service = AIService()
    try:
        result = ai_service.generate_swot_analysis(
            hospital_name=request.hospital_name,
            competitor_info=request.competitor_info
        )
        return {"report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 분석 오류: {str(e)}")

@router.post("/assistant/benchmark-diagnosis")
def benchmark_diagnosis(
    request: BenchmarkDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """업종 평균 대비 벤치마크 AI 진단"""
    try:
        validated_id = UUID(request.client_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid client_id format")

    benchmark_service = BenchmarkService(db)
    ai_service = AIService()

    benchmark_data = benchmark_service.compare_client_performance(validated_id)
    try:
        report = ai_service.generate_deep_diagnosis(benchmark_data)
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 진단 오류: {str(e)}")

@router.post("/assistant/query")
def assistant_query(
    request: AssistantQueryRequest,
    db: Session = Depends(get_db)
):
    """
    자연어 질의 또는 빠른 질문 ID를 받아 적절한 AI 분석 결과 반환.
    query 값이 QUICK_QUERIES의 id와 일치하면 해당 분석 수행.
    """
    query = request.query.strip()
    client_id = request.client_id
    ai_service = AIService()
    service = AnalysisService(db)

    # 빠른 질문: 효율성/현황
    if query in ("status", "advice", "budget"):
        if not client_id or client_id in ("undefined", "null"):
            return {"report": "업체를 먼저 선택해주세요.", "type": "error"}
        try:
            validated_id = str(UUID(client_id))
        except (ValueError, TypeError):
            return {"report": "업체 ID가 올바르지 않습니다.", "type": "error"}

        data = service.get_efficiency_data(validated_id, days=30)
        if not data["items"]:
            return {"report": "광고 집행 데이터가 없어 분석할 수 없습니다.", "type": "info"}

        ai_res = ai_service.generate_efficiency_review(data)
        if query == "status":
            return {"report": ai_res.get("overall", "분석 결과 없음"), "type": "markdown"}
        elif query == "advice":
            suggestions = ai_res.get("suggestions", {})
            lines = [f"**{k}**: {v}" for k, v in suggestions.items()]
            return {"report": "\n\n".join(lines) if lines else "개선 제안이 없습니다.", "type": "markdown"}
        elif query == "budget":
            from app.services.roi_optimizer import ROIOptimizerService
            roi_service = ROIOptimizerService(db)
            roas_data = roi_service.track_campaign_roas(UUID(validated_id), days=30)
            top = roas_data["campaigns"][:3] if roas_data["campaigns"] else []
            lines = [f"**{c['campaign_name']}** — ROAS {c['roas']}%로 예산 집중 추천" for c in top]
            return {
                "report": "**예산 집중 추천 캠페인 (ROAS 상위)**\n\n" + "\n\n".join(lines) if lines else "캠페인 데이터가 없습니다.",
                "type": "markdown"
            }

    # 빠른 질문: 상위 키워드
    elif query == "top_keyword":
        if not client_id or client_id in ("undefined", "null"):
            return {"report": "업체를 먼저 선택해주세요.", "type": "error"}
        try:
            validated_id = UUID(client_id)
        except (ValueError, TypeError):
            return {"report": "업체 ID가 올바르지 않습니다.", "type": "error"}
        from app.models.models import DailyRank, Keyword, Target, TargetType
        from sqlalchemy import func, and_
        import datetime
        week_ago = datetime.date.today() - datetime.timedelta(days=7)
        top_kws = db.query(
            Keyword.term,
            func.count(DailyRank.id).label("cnt")
        ).join(DailyRank, DailyRank.keyword_id == Keyword.id).filter(
            and_(
                DailyRank.client_id == validated_id,
                DailyRank.captured_at >= week_ago
            )
        ).group_by(Keyword.term).order_by(func.count(DailyRank.id).desc()).limit(5).all()

        if not top_kws:
            return {"report": "최근 7일 내 수집된 순위 데이터가 없습니다.", "type": "info"}
        lines = [f"{i+1}. **{kw.term}** — {kw.cnt}회 노출" for i, kw in enumerate(top_kws)]
        return {"report": "**최근 7일 상위 노출 키워드**\n\n" + "\n\n".join(lines), "type": "markdown"}

    # 빠른 질문: SWOT
    elif query == "swot":
        if not client_id or client_id in ("undefined", "null"):
            return {"report": "업체를 먼저 선택해주세요.", "type": "error"}
        try:
            validated_id = UUID(client_id)
        except (ValueError, TypeError):
            return {"report": "업체 ID가 올바르지 않습니다.", "type": "error"}
        client = db.query(Client).filter(Client.id == validated_id).first()
        hospital_name = client.name if client else "해당 병원"
        report = ai_service.generate_swot_analysis(hospital_name=hospital_name, competitor_info=[])
        return {"report": report, "type": "markdown"}

    # 자유 질의: Gemini에 직접 전달
    else:
        if not ai_service.client:
            return {"report": "AI 서비스가 설정되지 않았습니다. GOOGLE_API_KEY를 확인해주세요.", "type": "error"}
        try:
            context = ""
            if client_id and client_id not in ("undefined", "null", None):
                try:
                    validated_id = str(UUID(client_id))
                    data = service.get_efficiency_data(validated_id, days=30)
                    if data["items"]:
                        top = data["items"][:3]
                        context = f"\n\n[현재 업체 데이터 요약]\n총 광고비: {data['total_spend']:,}원, 전환수: {data['total_conversions']}건, ROAS: {data['overall_roas']}%\n상위 캠페인: {', '.join(c['name'] for c in top)}"
                except Exception:
                    pass

            prompt = f"""당신은 치과 마케팅 전문 AI 어시스턴트입니다. 한국어로 답변해주세요.
{context}

질문: {query}

답변 (마크다운 형식으로, 간결하고 실용적으로):"""

            response = ai_service.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return {"report": response.text, "type": "markdown"}
        except Exception as e:
            return {"report": f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}", "type": "error"}


# ---------------------------------------------------------------------------
# Phase 6-2: SSE 스트리밍 + 대화 히스토리
# ---------------------------------------------------------------------------

class StreamQueryRequest(BaseModel):
    query: str
    client_id: Optional[str] = None
    session_id: Optional[str] = None  # 기존 세션에 이어쓰기


class ChatSessionCreateRequest(BaseModel):
    client_id: Optional[str] = None


class ChatMessageSchema(BaseModel):
    id: str
    role: str
    content: str
    msg_type: Optional[str] = "text"
    created_at: str


class ChatSessionSchema(BaseModel):
    id: str
    title: Optional[str]
    client_id: Optional[str]
    created_at: str
    messages: List[ChatMessageSchema] = []


def _handle_quick_query(
    query: str,
    client_id: Optional[str],
    db: Session,
    service: "AnalysisService",
    ai_service: "AIService",
) -> str:
    """quick-query ID → 분석 결과 텍스트 반환 (stream 엔드포인트에서 재사용)"""
    if query in ("status", "advice", "budget"):
        if not client_id or client_id in ("undefined", "null", None):
            return "업체를 먼저 선택해주세요."
        try:
            validated_id = str(UUID(client_id))
        except (ValueError, TypeError):
            return "업체 ID가 올바르지 않습니다."
        data = service.get_efficiency_data(validated_id, days=30)
        if not data["items"]:
            return "광고 집행 데이터가 없어 분석할 수 없습니다."
        ai_res = ai_service.generate_efficiency_review(data)
        if query == "status":
            return ai_res.get("overall", "분석 결과 없음")
        elif query == "advice":
            suggestions = ai_res.get("suggestions", {})
            lines = [f"**{k}**: {v}" for k, v in suggestions.items()]
            return "\n\n".join(lines) if lines else "개선 제안이 없습니다."
        elif query == "budget":
            from app.services.roi_optimizer import ROIOptimizerService
            roi_service = ROIOptimizerService(db)
            roas_data = roi_service.track_campaign_roas(UUID(validated_id), days=30)
            top = roas_data["campaigns"][:3] if roas_data["campaigns"] else []
            lines = [f"**{c['campaign_name']}** — ROAS {c['roas']}%로 예산 집중 추천" for c in top]
            return "**예산 집중 추천 캠페인 (ROAS 상위)**\n\n" + "\n\n".join(lines) if lines else "캠페인 데이터가 없습니다."

    elif query == "top_keyword":
        if not client_id or client_id in ("undefined", "null", None):
            return "업체를 먼저 선택해주세요."
        try:
            validated_id = UUID(client_id)
        except (ValueError, TypeError):
            return "업체 ID가 올바르지 않습니다."
        from app.models.models import DailyRank, Keyword
        from sqlalchemy import func, and_
        import datetime
        week_ago = datetime.date.today() - datetime.timedelta(days=7)
        top_kws = db.query(
            Keyword.term, func.count(DailyRank.id).label("cnt")
        ).join(DailyRank, DailyRank.keyword_id == Keyword.id).filter(
            and_(DailyRank.client_id == validated_id, DailyRank.captured_at >= week_ago)
        ).group_by(Keyword.term).order_by(func.count(DailyRank.id).desc()).limit(5).all()
        if not top_kws:
            return "최근 7일 내 수집된 순위 데이터가 없습니다."
        lines = [f"{i+1}. **{kw.term}** — {kw.cnt}회 노출" for i, kw in enumerate(top_kws)]
        return "**최근 7일 상위 노출 키워드**\n\n" + "\n\n".join(lines)

    elif query == "swot":
        if not client_id or client_id in ("undefined", "null", None):
            return "업체를 먼저 선택해주세요."
        try:
            validated_id = UUID(client_id)
        except (ValueError, TypeError):
            return "업체 ID가 올바르지 않습니다."
        client = db.query(Client).filter(Client.id == validated_id).first()
        hospital_name = client.name if client else "해당 병원"
        return ai_service.generate_swot_analysis(hospital_name=hospital_name, competitor_info=[])

    return f"알 수 없는 빠른 질문 ID: {query}"


def _build_prompt(
    query: str,
    client_id: Optional[str],
    db: Session,
    service: "AnalysisService",
    history: Optional[list] = None,
) -> str:
    """자유 질의용 Gemini 프롬프트 빌더 (대화 히스토리 포함)"""
    from app.models.models import ChatSession, ChatMessage  # noqa: F811

    # 업체 데이터 컨텍스트
    context = ""
    if client_id and client_id not in ("undefined", "null", None):
        try:
            validated_id = str(UUID(client_id))
            data = service.get_efficiency_data(validated_id, days=30)
            if data["items"]:
                top = data["items"][:3]
                context = (
                    f"\n\n[현재 업체 데이터 요약]\n"
                    f"총 광고비: {data['total_spend']:,}원, 전환수: {data['total_conversions']}건, ROAS: {data['overall_roas']}%\n"
                    f"상위 캠페인: {', '.join(c['name'] for c in top)}"
                )
        except Exception:
            pass

    # 대화 히스토리 (최근 10턴 = 20개 메시지 이내)
    history_text = ""
    if history:
        recent = history[-20:]
        lines = []
        for msg in recent:
            role_label = "사용자" if msg["role"] == "user" else "어시스턴트"
            lines.append(f"{role_label}: {msg['content']}")
        history_text = "\n\n[이전 대화]\n" + "\n".join(lines)

    return (
        f"당신은 치과 마케팅 전문 AI 어시스턴트입니다. 한국어로 답변해주세요.{context}{history_text}\n\n"
        f"질문: {query}\n\n답변 (마크다운 형식으로, 간결하고 실용적으로):"
    )


@router.post("/assistant/stream")
def assistant_stream(
    request: StreamQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    SSE 스트리밍 응답. Gemini generate_content_stream 사용.
    대화 내용을 DB에 저장 (session_id 활용).
    """
    from app.models.models import ChatSession, ChatMessage
    import uuid as uuid_mod

    ai_service = AIService()
    service = AnalysisService(db)
    query = request.query.strip()
    client_id = request.client_id

    # --- 세션 생성 or 재사용 ---
    session_id = request.session_id
    session_obj = None
    if session_id:
        try:
            session_obj = db.query(ChatSession).filter(ChatSession.id == UUID(session_id)).first()
        except Exception:
            session_obj = None

    if not session_obj:
        # 새 세션 생성: 제목은 첫 질문 앞 20자
        client_uuid = None
        if client_id and client_id not in ("undefined", "null", None):
            try:
                client_uuid = UUID(client_id)
            except Exception:
                pass
        session_obj = ChatSession(
            user_id=current_user.id,
            client_id=client_uuid,
            title=query[:40] if query else "새 대화",
        )
        db.add(session_obj)
        db.flush()

    # 세션의 기존 메시지 로드 (히스토리)
    existing_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_obj.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in existing_messages]

    # 사용자 메시지 저장
    user_msg = ChatMessage(
        session_id=session_obj.id,
        role="user",
        content=query,
        msg_type="text",
    )
    db.add(user_msg)
    db.flush()
    new_session_id = str(session_obj.id)

    # --- 프롬프트 빌드 ---
    # quick-query ID인 경우 구조화된 데이터 응답으로 전환
    quick_ids = {q["id"] for q in QUICK_QUERIES}

    if not ai_service.client:
        # AI 미설정 시 즉시 응답
        err_content = "AI 서비스가 설정되지 않았습니다."
        ai_msg = ChatMessage(session_id=session_obj.id, role="assistant", content=err_content, msg_type="error")
        db.add(ai_msg)
        db.commit()

        def error_gen():
            yield f"data: {json.dumps({'delta': err_content, 'done': False, 'session_id': new_session_id})}\n\n"
            yield f"data: {json.dumps({'delta': '', 'done': True, 'session_id': new_session_id})}\n\n"

        return StreamingResponse(error_gen(), media_type="text/event-stream")

    # quick-query ID인 경우 기존 query 엔드포인트 로직으로 텍스트 생성 후 스트리밍
    if query in quick_ids:
        # 동기적으로 분석 결과 생성 후 단일 청크로 스트리밍
        try:
            result_text = _handle_quick_query(query, client_id, db, service, ai_service)
        except Exception as e:
            result_text = f"분석 중 오류가 발생했습니다: {str(e)}"

        ai_msg_q = ChatMessage(
            session_id=session_obj.id,
            role="assistant",
            content=result_text,
            msg_type="markdown",
        )
        db.add(ai_msg_q)
        db.commit()

        def quick_stream():
            # 단어 단위로 나눠 스트리밍 느낌 부여
            words = result_text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'delta': chunk, 'done': False, 'session_id': new_session_id}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'delta': '', 'done': True, 'session_id': new_session_id}, ensure_ascii=False)}\n\n"

        return StreamingResponse(quick_stream(), media_type="text/event-stream")

    prompt = _build_prompt(query, client_id, db, service, history=history)

    def event_stream():
        full_response = []
        try:
            for chunk in ai_service.client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=prompt,
            ):
                if chunk.text:
                    full_response.append(chunk.text)
                    payload = json.dumps({"delta": chunk.text, "done": False, "session_id": new_session_id}, ensure_ascii=False)
                    yield f"data: {payload}\n\n"
        except Exception as e:
            err = f"AI 스트리밍 오류: {str(e)}"
            full_response.append(err)
            payload = json.dumps({"delta": err, "done": False, "session_id": new_session_id}, ensure_ascii=False)
            yield f"data: {payload}\n\n"

        # 스트리밍 완료 — DB에 어시스턴트 메시지 저장
        full_text = "".join(full_response)
        ai_msg = ChatMessage(
            session_id=session_obj.id,
            role="assistant",
            content=full_text,
            msg_type="markdown",
        )
        db.add(ai_msg)
        db.commit()

        yield f"data: {json.dumps({'delta': '', 'done': True, 'session_id': new_session_id}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/scrape-results/{client_id}")
def get_scrape_results(
    client_id: str,
    keyword: Optional[str] = None,
    platform: str = "NAVER_PLACE",
    db: Session = Depends(get_db),
):
    """
    실제 스크래핑 결과 조회 (DailyRank 테이블에서)
    
    Args:
        client_id: 클라이언트 ID
        keyword: (선택) 특정 키워드만 조회
        platform: (기본값: NAVER_PLACE) 플랫폼 타입
        
    Returns:
        {
            "has_data": 데이터 존재 여부,
            "keyword": 검색 키워드,
            "platform": 플랫폼,
            "results": 순위 데이터 배열,
            "total_count": 결과 총 개수
        }
    """
    try:
        client_uuid = UUID(client_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid client_id format")
    
    # 클라이언트 존재 확인
    client = db.query(Client).filter(Client.id == client_uuid).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 키워드 객체 조회 (지정된 경우)
    keyword_obj = None
    if keyword:
        keyword_obj = db.query(Keyword).filter(
            Keyword.term == keyword,
            Keyword.client_id == client_uuid
        ).first()
    
    # DailyRank 조회
    query = db.query(DailyRank).filter(DailyRank.client_id == client_uuid)
    
    if keyword_obj:
        query = query.filter(DailyRank.keyword_id == keyword_obj.id)
    
    # 최신 데이터 먼저 정렬
    results = query.order_by(DailyRank.captured_at.desc()).all()
    
    # 응답 구성
    results_list = []
    for r in results:
        result_item = {
            "rank": r.rank,
            "rank_change": r.rank_change,
            "target_name": r.target.name if r.target else None,
            "target_type": r.target.type.value if r.target and r.target.type else None,
            "link": r.target.urls.get("default") if r.target and r.target.urls else None,
            "captured_at": r.captured_at.isoformat() if r.captured_at else None,
        }
        results_list.append(result_item)
    
    return {
        "has_data": len(results_list) > 0,
        "keyword": keyword,
        "platform": platform,
        "results": results_list,
        "total_count": len(results_list),
    }


@router.get("/assistant/sessions")
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """현재 사용자의 대화 세션 목록 (최근 20개)"""
    from app.models.models import ChatSession
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "client_id": str(s.client_id) if s.client_id else None,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/assistant/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """특정 세션의 메시지 전체 조회"""
    from app.models.models import ChatSession, ChatMessage
    try:
        sid = UUID(session_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = db.query(ChatSession).filter(ChatSession.id == sid, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": str(session.id),
        "title": session.title,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "msg_type": m.msg_type,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ],
    }


@router.delete("/assistant/sessions/{session_id}")
def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """대화 세션 삭제"""
    from app.models.models import ChatSession
    try:
        sid = UUID(session_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = db.query(ChatSession).filter(ChatSession.id == sid, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"ok": True}
