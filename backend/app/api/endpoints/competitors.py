from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.competitor_intelligence import CompetitorIntelligenceService
from app.models.models import PlatformType, User
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel
from typing import List, Dict, Optional
from uuid import UUID

router = APIRouter(tags=["Competitor Intelligence"])

class CompetitorDiscoveryRequest(BaseModel):
    client_id: UUID
    platform: PlatformType = PlatformType.NAVER_PLACE
    keyword_overlap_threshold: float = 0.3
    min_appearances: int = 3
    top_n: int = 10
    days: int = 30

class CompetitorStrategyRequest(BaseModel):
    target_id: UUID
    platform: PlatformType = PlatformType.NAVER_AD
    days: int = 30

@router.post("/discover")
def discover_competitors(
    request: CompetitorDiscoveryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    키워드 중복도 기반 경쟁사 자동 발굴

    **알고리즘**:
    1. 클라이언트가 추적 중인 키워드 목록 추출
    2. 해당 키워드들의 랭킹 데이터에서 자주 등장하는 타겟 식별
    3. 키워드 중복도 계산 (Jaccard Similarity)
    4. 중복도가 높은 타겟을 경쟁사로 분류

    **Parameters**:
    - `client_id`: 분석 대상 클라이언트 ID
    - `platform`: 분석 플랫폼 (NAVER_PLACE, NAVER_VIEW 등)
    - `keyword_overlap_threshold`: 키워드 중복도 임계값 (0.0~1.0, 기본 0.3)
    - `min_appearances`: 최소 등장 횟수 (기본 3회)
    - `top_n`: 상위 N개 경쟁사만 반환 (기본 10개)
    - `days`: 분석 기간 (기본 30일)

    **Response**:
    ```json
    [
        {
            "target_id": "uuid",
            "name": "경쟁사 이름",
            "type": "COMPETITOR",
            "overlap_score": 0.65,
            "shared_keywords": 13,
            "total_keywords": 20,
            "keywords_appeared": 15,
            "shared_keyword_terms": ["임플란트", "치아교정", ...]
        }
    ]
    ```
    """
    service = CompetitorIntelligenceService(db)

    try:
        competitors = service.discover_competitors(
            client_id=request.client_id,
            platform=request.platform,
            keyword_overlap_threshold=request.keyword_overlap_threshold,
            min_appearances=request.min_appearances,
            top_n=request.top_n,
            days=request.days
        )

        return {
            "status": "SUCCESS",
            "count": len(competitors),
            "competitors": competitors,
            "parameters": {
                "client_id": str(request.client_id),
                "platform": request.platform.value,
                "threshold": request.keyword_overlap_threshold,
                "days": request.days
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/strategy-analysis")
def analyze_competitor_strategy(
    request: CompetitorStrategyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    경쟁사 광고 전략 심층 분석

    **분석 항목**:
    1. 주력 키워드 (랭킹 데이터 기반)
    2. 광고 집행 패턴 (시간대별, 요일별 활동)
    3. 순위 트렌드 (최근 상승/하락 추세)

    **Parameters**:
    - `target_id`: 분석 대상 타겟(경쟁사) ID
    - `platform`: 분석 플랫폼 (기본 NAVER_AD)
    - `days`: 분석 기간 (기본 30일)

    **Response**:
    ```json
    {
        "target_id": "uuid",
        "target_name": "경쟁사A",
        "platform": "NAVER_AD",
        "analysis_period": "2026-01-17 ~ 2026-02-17",
        "top_keywords": [
            {
                "term": "임플란트",
                "appearances": 45,
                "avg_rank": 2.3,
                "best_rank": 1
            }
        ],
        "activity_by_hour": {"9": 12, "10": 15, ...},
        "activity_by_dow": {"월": 10, "화": 8, ...},
        "rank_trend": [
            {"date": "2026-01-17", "avg_rank": 3.2},
            ...
        ],
        "trend_direction": "상승"
    }
    ```
    """
    service = CompetitorIntelligenceService(db)

    try:
        analysis = service.analyze_competitor_strategy(
            target_id=request.target_id,
            platform=request.platform,
            days=request.days
        )

        return {
            "status": "SUCCESS",
            "analysis": analysis
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positioning-map/{client_id}")
def get_keyword_positioning_map(
    client_id: UUID,
    platform: PlatformType = Query(PlatformType.NAVER_PLACE),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    키워드 포지셔닝 맵 데이터 조회

    클라이언트와 주요 경쟁사들의 키워드별 순위를 비교 시각화하기 위한 데이터

    **사용 예시**:
    프론트엔드에서 히트맵 또는 매트릭스 차트로 시각화
    - X축: 키워드
    - Y축: 타겟(업체)
    - 셀 값: 순위 (색상으로 표현)

    **Response**:
    ```json
    {
        "keywords": ["임플란트", "치아교정", "스케일링"],
        "targets": [
            {
                "id": "uuid",
                "name": "우리 병원",
                "type": "OWNER",
                "ranks": [1, 3, 2]
            },
            {
                "id": "uuid",
                "name": "경쟁사A",
                "type": "COMPETITOR",
                "ranks": [2, 1, null]
            }
        ],
        "snapshot_time": "2026-02-17T14:30:00"
    }
    ```
    """
    service = CompetitorIntelligenceService(db)

    try:
        positioning_map = service.get_keyword_positioning_map(
            client_id=client_id,
            platform=platform,
            days=days
        )

        return {
            "status": "SUCCESS",
            "data": positioning_map
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
