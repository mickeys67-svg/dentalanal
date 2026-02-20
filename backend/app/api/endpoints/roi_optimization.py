from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.roi_optimizer import ROIOptimizerService
from app.models.models import User
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

router = APIRouter(tags=["ROI Optimization"])

class ROASTrackingRequest(BaseModel):
    client_id: UUID
    days: int = 30
    conversion_value: Optional[float] = None  # None이면 클라이언트 DB 설정값 사용

@router.post("/track-roas")
def track_campaign_roas(
    request: ROASTrackingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    캠페인별 ROAS 추적 및 트렌드 분석

    **Response**:
    ```json
    {
        "period": "2026-01-17 ~ 2026-02-17",
        "campaigns": [
            {
                "campaign_id": "uuid",
                "campaign_name": "브랜드_임플란트",
                "platform": "NAVER_AD",
                "total_spend": 1500000,
                "total_conversions": 25,
                "roas": 250.0,
                "cpa": 60000,
                "ctr": 2.5,
                "cvr": 5.0,
                "trend": [
                    {"date": "2026-01-17", "roas": 230},
                    {"date": "2026-01-18", "roas": 250},
                    ...
                ]
            }
        ],
        "summary": {
            "total_campaigns": 5,
            "avg_roas": 180.5,
            "best_performer": "브랜드_임플란트",
            "worst_performer": "디스플레이_리타겟팅"
        }
    }
    ```
    """
    service = ROIOptimizerService(db)

    try:
        result = service.track_campaign_roas(
            client_id=request.client_id,
            days=request.days,
            conversion_value=request.conversion_value
        )

        return {
            "status": "SUCCESS",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detect-inefficient/{client_id}")
def detect_inefficient_ads(
    client_id: UUID,
    days: int = Query(30, ge=7, le=90),
    conversion_value: Optional[float] = Query(None, gt=0),
    create_alerts: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    비효율 광고 자동 감지

    **감지 기준**:
    1. ROAS가 임계값(50%) 이하
    2. CTR이 업종 평균(0.5%) 이하
    3. CPA가 상위 75% 이상 (동일 클라이언트 내 비교)

    **Parameters**:
    - `client_id`: 클라이언트 ID
    - `days`: 분석 기간 (7~90일)
    - `conversion_value`: 전환당 평균 수익 (기본 150,000원)
    - `create_alerts`: 알림 자동 생성 여부 (기본 false)

    **Response**:
    ```json
    [
        {
            "campaign_id": "uuid",
            "campaign_name": "디스플레이_리타겟팅",
            "platform": "NAVER_AD",
            "spend": 500000,
            "roas": 35.0,
            "ctr": 0.3,
            "cpa": 125000,
            "severity": "high",
            "issues": [
                "ROAS가 35.0%로 목표(50%) 미달",
                "CTR이 0.3%로 업종 평균(0.5%) 미달"
            ],
            "recommendations": [
                "전환율 개선을 위해 타겟팅 및 키워드를 재검토하세요",
                "광고 소재(제목, 이미지)를 A/B 테스트하세요"
            ]
        }
    ]
    ```
    """
    service = ROIOptimizerService(db)

    try:
        inefficient_ads = service.detect_inefficient_ads(
            client_id=client_id,
            days=days,
            conversion_value=conversion_value
        )

        # 알림 생성 옵션
        if create_alerts:
            service.create_alert_for_inefficiency(client_id, inefficient_ads)

        return {
            "status": "SUCCESS",
            "count": len(inefficient_ads),
            "inefficient_ads": inefficient_ads
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/budget-reallocation/{client_id}")
def recommend_budget_reallocation(
    client_id: UUID,
    days: int = Query(30, ge=7, le=90),
    conversion_value: Optional[float] = Query(None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    예산 재분배 추천

    **알고리즘**:
    1. ROAS 상위 20% 캠페인: 예산 증액 권장 (+20%)
    2. ROAS 하위 20% 캠페인: 예산 감액 권장 (-30%)
    3. 중간 캠페인: 유지 권장

    **Response**:
    ```json
    {
        "period": "2026-01-17 ~ 2026-02-17",
        "current_total_budget": 5000000,
        "recommended_total_budget": 4700000,
        "net_change": -300000,
        "recommendations": [
            {
                "campaign_name": "브랜드_임플란트",
                "current_spend": 1500000,
                "recommended_spend": 1800000,
                "change": "+300000원 (+20%)",
                "action": "증액",
                "reason": "ROAS 250%로 우수한 성과",
                "roas": 250
            },
            {
                "campaign_name": "디스플레이_리타겟팅",
                "current_spend": 500000,
                "recommended_spend": 350000,
                "change": "-150000원 (-30%)",
                "action": "감액",
                "reason": "ROAS 35%로 비효율적",
                "roas": 35
            }
        ],
        "summary": {
            "campaigns_to_increase": 2,
            "campaigns_to_decrease": 2,
            "total_increase_amount": 600000,
            "total_decrease_amount": 900000
        }
    }
    ```
    """
    service = ROIOptimizerService(db)

    try:
        recommendations = service.recommend_budget_reallocation(
            client_id=client_id,
            days=days,
            conversion_value=conversion_value
        )

        return {
            "status": "SUCCESS",
            "data": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
