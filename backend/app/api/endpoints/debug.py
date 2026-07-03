"""
🔍 데이터 디버깅 API 엔드포인트

사용:
  GET /api/v1/debug/diagnose
  
응답:
  - 데이터베이스 테이블 상태
  - 현재 데이터 통계
  - 식별된 문제점
  - 권장 해결책
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
from app.debug.data_diagnostic import DataDiagnostic
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependencies
def get_get_current_user():
    """Dynamically import get_current_user to avoid circular imports"""
    from app.api.endpoints.auth import get_current_user
    return get_current_user


@router.get("/diagnose")
async def run_data_diagnostic(
    current_user: User = Depends(lambda: get_get_current_user()),
    db: Session = Depends(get_db)
):
    """
    데이터 디버깅 진단 실행
    
    🔒 인증 필수 (슈퍼 어드민만)
    
    Returns:
        - timestamp: 진단 실행 시간
        - sections: 각 섹션별 진단 결과
        - issues: 발견된 문제점
        - recommendations: 권장사항
    """
    
    # 권한 확인 (어드민 이상 접근 가능)
    if current_user.role not in ["SUPER_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Admin 이상의 권한이 필요합니다"
        )
    
    try:
        logger.info(f"[Debug] 진단 시작 (사용자: {current_user.email})")
        
        diagnostic = DataDiagnostic(db)
        await diagnostic.run_full_diagnosis()
        report = diagnostic.generate_summary()
        
        logger.info(f"[Debug] 진단 완료")
        
        return {
            "status": "success",
            "data": report
        }
    
    except Exception as e:
        logger.error(f"[Debug] 진단 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"진단 실패: {str(e)}"
        )


@router.get("/stats")
async def get_quick_stats(
    current_user: User = Depends(lambda: get_get_current_user()),
    db: Session = Depends(get_db)
):
    """
    빠른 통계 조회 (진단 없이 즉시)
    
    Returns:
        - clients: 클라이언트 수
        - keywords: 키워드 수
        - daily_ranks: 일일 순위 기록 수
        - analysis_history: 분석 이력 수
    """
    
    try:
        from app.models.models import Client, Keyword, DailyRank, AnalysisHistory
        
        stats = {
            "clients": db.query(Client).count(),
            "keywords": db.query(Keyword).count(),
            "daily_ranks": db.query(DailyRank).count(),
            "analysis_history": db.query(AnalysisHistory).count(),
        }
        
        return {
            "status": "success",
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"[Stats] 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 실패: {str(e)}"
        )


@router.get("/trace-keyword/{keyword}")
async def trace_keyword_flow(
    keyword: str,
    client_id: str = None,
    current_user: User = Depends(lambda: get_get_current_user()),
    db: Session = Depends(get_db)
):
    """
    특정 키워드의 데이터 흐름 추적
    
    Parameters:
        - keyword: 추적할 키워드 (예: "다이어트")
        - client_id: 클라이언트 ID (선택사항)
    
    Returns:
        - keyword_data: 키워드 정보
        - daily_ranks: 수집된 순위 기록
        - analysis_history: 분석 이력
    """
    
    try:
        from app.models.models import Keyword, DailyRank, AnalysisHistory
        
        logger.info(f"[Trace] 키워드 추적: {keyword} (Client: {client_id})")
        
        # 키워드 찾기
        kw_query = db.query(Keyword).filter(Keyword.term == keyword)
        if client_id:
            kw_query = kw_query.filter(Keyword.client_id == client_id)
        
        keyword_data = kw_query.first()
        
        if not keyword_data:
            raise HTTPException(
                status_code=404,
                detail=f"키워드를 찾을 수 없습니다: {keyword}"
            )
        
        # 일일 순위 기록
        daily_ranks = db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword_data.id
        ).all()
        
        # 분석 이력
        analysis_history = db.query(AnalysisHistory).filter(
            AnalysisHistory.keyword == keyword
        )
        if client_id:
            analysis_history = analysis_history.filter(
                AnalysisHistory.client_id == client_id
            )
        analysis_history = analysis_history.all()
        
        return {
            "status": "success",
            "data": {
                "keyword": keyword_data.term,
                "client_id": str(keyword_data.client_id),
                "daily_ranks_count": len(daily_ranks),
                "analysis_history_count": len(analysis_history),
                "recent_ranks": [
                    {
                        "rank": dr.rank,
                        "platform": str(dr.platform),
                        "captured_at": dr.captured_at.isoformat(),
                    }
                    for dr in sorted(daily_ranks, key=lambda x: x.captured_at, reverse=True)[:5]
                ],
                "recent_analysis": [
                    {
                        "is_saved": ah.is_saved,
                        "created_at": ah.created_at.isoformat(),
                    }
                    for ah in sorted(analysis_history, key=lambda x: x.created_at, reverse=True)[:5]
                ]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Trace] 추적 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"추적 실패: {str(e)}"
        )


@router.get("/connections-status")
async def get_connections_status(
    current_user: User = Depends(lambda: get_get_current_user()),
    db: Session = Depends(get_db)
):
    """
    플랫폼 연결 상태 확인
    
    Returns:
        - connections: 각 플랫폼별 연결 상태
        - last_sync: 마지막 동기화 시간
    """
    
    try:
        from app.models.models import PlatformConnection
        
        connections = db.query(PlatformConnection).all()
        
        status_data = {}
        for conn in connections:
            platform = str(conn.platform)
            if platform not in status_data:
                status_data[platform] = {
                    "total": 0,
                    "active": 0,
                    "inactive": 0
                }
            
            status_data[platform]["total"] += 1
            if conn.is_active:
                status_data[platform]["active"] += 1
            else:
                status_data[platform]["inactive"] += 1
        
        return {
            "status": "success",
            "data": {
                "connections": status_data,
                "total_connections": len(connections)
            }
        }
    
    except Exception as e:
        logger.error(f"[Connections] 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"연결 상태 조회 실패: {str(e)}"
        )
