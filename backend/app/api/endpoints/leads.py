from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Lead, LeadActivity, LeadProfile, LeadEvent, User, PlatformType
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel, ConfigDict
from uuid import UUID
import uuid
import datetime

router = APIRouter(tags=["Leads"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    client_id: UUID
    name: Optional[str] = None
    contact: Optional[str] = None
    channel: Optional[str] = None          # organic, paid, social, referral
    first_visit_date: Optional[datetime.datetime] = None

class LeadResponse(BaseModel):
    id: UUID
    client_id: UUID
    name: Optional[str] = None
    contact: Optional[str] = None
    channel: Optional[str] = None
    cohort_month: str
    first_visit_date: datetime.datetime
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class LeadActivityCreate(BaseModel):
    activity_month: str        # 'YYYY-MM'
    visits: int = 0
    conversions: int = 0
    revenue: float = 0.0

class LeadSummary(BaseModel):
    total_leads: int
    new_this_month: int
    total_conversions: int
    total_revenue: float
    conversion_rate: float
    by_channel: dict


# ─── Endpoints ────────────────────────────────────────────────────────────────
# NOTE: 구체적 경로(/summary/, /cohort/, /list/)를 /{id} 경로보다 먼저 선언해야
#       FastAPI 라우팅이 올바르게 동작함.

@router.get("/summary/{client_id}", response_model=LeadSummary)
def get_lead_summary(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """클라이언트의 리드 요약 통계"""
    total_leads = db.query(func.count(Lead.id)).filter(Lead.client_id == client_id).scalar() or 0

    this_month = datetime.date.today().strftime("%Y-%m")
    new_this_month = db.query(func.count(Lead.id)).filter(
        Lead.client_id == client_id,
        Lead.cohort_month == this_month
    ).scalar() or 0

    # [FIX] N+1 제거: JOIN으로 단일 쿼리
    totals = db.query(
        func.sum(LeadActivity.conversions).label("total_conv"),
        func.sum(LeadActivity.revenue).label("total_rev"),
    ).join(Lead, Lead.id == LeadActivity.lead_id)\
     .filter(Lead.client_id == client_id)\
     .first()

    total_conversions = int(totals.total_conv or 0) if totals else 0
    total_revenue = float(totals.total_rev or 0.0) if totals else 0.0
    conversion_rate = round(total_conversions / total_leads * 100, 1) if total_leads > 0 else 0.0

    # 채널별 분포
    channel_rows = db.query(Lead.channel, func.count(Lead.id).label("cnt")).filter(
        Lead.client_id == client_id
    ).group_by(Lead.channel).all()
    by_channel = {(r.channel or "unknown"): r.cnt for r in channel_rows}

    return LeadSummary(
        total_leads=total_leads,
        new_this_month=new_this_month,
        total_conversions=total_conversions,
        total_revenue=total_revenue,
        conversion_rate=conversion_rate,
        by_channel=by_channel,
    )


# [FIX] 코호트 엔드포인트: /{lead_id}/cohort → /cohort/{client_id}
# 이전 경로는 /{client_id} GET 핸들러와 라우트 충돌로 실제 호출 불가능했음
@router.get("/cohort/{client_id}")
def get_cohort_data(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """코호트 분석 - 월별 리드 유입 및 전환율 추이"""
    rows = db.query(
        Lead.cohort_month,
        func.count(Lead.id).label("total"),
        func.sum(LeadActivity.conversions).label("conversions"),
        func.sum(LeadActivity.revenue).label("revenue"),
    ).outerjoin(LeadActivity, Lead.id == LeadActivity.lead_id)\
     .filter(Lead.client_id == client_id)\
     .group_by(Lead.cohort_month)\
     .order_by(Lead.cohort_month).all()

    return [
        {
            "cohort_month": r.cohort_month,
            "total_leads": r.total,
            "conversions": int(r.conversions or 0),
            "revenue": float(r.revenue or 0),
            "conversion_rate": round(int(r.conversions or 0) / r.total * 100, 1) if r.total > 0 else 0,
        }
        for r in rows
    ]


# [NOTE] /{client_id}는 구체적 경로들보다 반드시 뒤에 위치해야 함
@router.get("/{client_id}", response_model=List[LeadResponse])
def get_leads(
    client_id: UUID,
    channel: Optional[str] = Query(None),
    cohort_month: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """클라이언트의 리드 목록 조회"""
    q = db.query(Lead).filter(Lead.client_id == client_id)
    if channel:
        q = q.filter(Lead.channel == channel)
    if cohort_month:
        q = q.filter(Lead.cohort_month == cohort_month)
    return q.order_by(Lead.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(
    data: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """리드 등록"""
    visit_dt = data.first_visit_date or datetime.datetime.utcnow()
    cohort_month = visit_dt.strftime("%Y-%m")

    lead = Lead(
        id=uuid.uuid4(),
        client_id=data.client_id,
        name=data.name,
        contact=data.contact,
        channel=data.channel,
        first_visit_date=visit_dt,
        cohort_month=cohort_month,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """리드 삭제 — cascade 관계가 있으나 명시적 삭제로 안전성 확보"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()


@router.post("/{lead_id}/activity", status_code=status.HTTP_201_CREATED)
def add_lead_activity(
    lead_id: UUID,
    data: LeadActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """리드 월별 활동 기록"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    activity = LeadActivity(
        id=uuid.uuid4(),
        lead_id=lead_id,
        activity_month=data.activity_month,
        visits=data.visits,
        conversions=data.conversions,
        revenue=data.revenue,
    )
    db.add(activity)
    db.commit()
    return {"status": "SUCCESS"}
