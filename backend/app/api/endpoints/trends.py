from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.trend_analysis import TrendAnalysisService
from app.models.models import User
from app.api.endpoints.auth import get_current_user
from typing import Optional
from uuid import UUID

router = APIRouter(tags=["Trend Analysis"])

@router.get("/seasonality/{client_id}")
def detect_seasonality(
    client_id: UUID,
    lookback_months: int = Query(12, ge=3, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    계절성 패턴 감지

    **분석 항목**:
    1. 월별 성과 변화 (MoM Growth)
    2. 요일별 성과 패턴
    3. 피크 시즌 식별

    **Response**:
    ```json
    {
        "analysis_period": "2025-02-17 ~ 2026-02-17",
        "monthly_performance": [
            {
                "year": 2025,
                "month": 3,
                "month_name": "March",
                "spend": 1500000,
                "clicks": 3500,
                "conversions": 45,
                "mom_growth": 12.5
            }
        ],
        "dow_performance": [
            {
                "day_of_week": "월요일",
                "spend": 200000,
                "clicks": 450,
                "conversions": 6
            }
        ],
        "peak_seasons": [
            {
                "year": 2025,
                "month": 12,
                "month_name": "December",
                "conversions": 85
            }
        ],
        "trend_summary": {
            "direction": "상승",
            "avg_mom_growth": 8.3
        }
    }
    ```
    """
    service = TrendAnalysisService(db)

    try:
        result = service.detect_seasonality(
            client_id=client_id,
            lookback_months=lookback_months
        )

        return {
            "status": "SUCCESS",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict-search-trends/{client_id}")
def predict_search_trends(
    client_id: UUID,
    keyword_id: Optional[UUID] = Query(None),
    days: int = Query(90, ge=30, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    검색 트렌드 예측

    Simple Moving Average (SMA) 기반 예측 모델

    **Response**:
    ```json
    {
        "analysis_period": "2025-11-17 ~ 2026-02-17",
        "predictions": {
            "임플란트": {
                "trend_data": [
                    {"date": "2025-11-17", "appearances": 12, "avg_rank": 3.5},
                    ...
                ],
                "recent_avg": 15.2,
                "overall_avg": 12.8,
                "prediction": "상승 추세"
            }
        }
    }
    ```
    """
    service = TrendAnalysisService(db)

    try:
        result = service.predict_search_trends(
            client_id=client_id,
            keyword_id=keyword_id,
            days=days
        )

        return {
            "status": "SUCCESS",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/ranking-drop/{client_id}")
def create_ranking_drop_alert(
    client_id: UUID,
    rank_drop_threshold: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    순위 급락 알림 생성

    전일 대비 순위가 {rank_drop_threshold}위 이상 하락한 키워드 감지

    **Response**:
    ```json
    {
        "status": "SUCCESS",
        "alerts_created": 3,
        "drops": [
            {
                "keyword_id": "uuid",
                "keyword": "임플란트",
                "previous_rank": 2,
                "current_rank": 8,
                "drop": 6
            }
        ]
    }
    ```
    """
    service = TrendAnalysisService(db)

    try:
        drops = service.create_ranking_drop_alert(
            client_id=client_id,
            rank_drop_threshold=rank_drop_threshold
        )

        return {
            "status": "SUCCESS",
            "alerts_created": len(drops),
            "drops": drops
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/budget-overspend/{client_id}")
def create_budget_overspend_alert(
    client_id: UUID,
    monthly_budget_limit: Optional[float] = Query(None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    예산 초과 알림 생성

    월 예산 대비 현재 소진율 체크 (80% 이상이면 경고)

    **Response**:
    ```json
    {
        "status": "SUCCESS",
        "alert_created": true,
        "budget_info": {
            "total_spend": 4500000,
            "budget_limit": 5000000,
            "utilization_rate": 90.0,
            "severity": "medium",
            "month": "2026-02"
        }
    }
    ```
    """
    service = TrendAnalysisService(db)

    try:
        budget_info = service.create_budget_overspend_alert(
            client_id=client_id,
            monthly_budget_limit=monthly_budget_limit
        )

        return {
            "status": "SUCCESS",
            "alert_created": budget_info is not None,
            "budget_info": budget_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
