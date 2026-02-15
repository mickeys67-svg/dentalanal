from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Client, Agency, User, UserRole
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel, ConfigDict
from uuid import UUID
import uuid
import datetime

router = APIRouter()

class ClientBase(BaseModel):
    name: str
    industry: str
    agency_id: Optional[UUID] = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: UUID
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    DEFAULT_AGENCY_ID = "00000000-0000-0000-0000-000000000000"
    
    if current_user.role == UserRole.SUPER_ADMIN:
        return db.query(Client).all()
    
    # Use user's agency_id if available, otherwise fallback to default agency
    agency_id = current_user.agency_id or UUID(DEFAULT_AGENCY_ID)
    
    return db.query(Client).filter(Client.agency_id == agency_id).order_by(Client.created_at.desc()).all()

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Create Client Request: {client_data.dict()} by User: {current_user.email}, Agency: {current_user.agency_id}")

    # Determine agency_id
    # SUPER_ADMIN can specify agency_id, others use their own
    # FIX: Default to '00000000-0000-0000-0000-000000000000' if user has no agency_id
    DEFAULT_AGENCY_ID = "00000000-0000-0000-0000-000000000000"
    
    agency_id = client_data.agency_id
    if current_user.role != UserRole.SUPER_ADMIN:
        agency_id = current_user.agency_id or UUID(DEFAULT_AGENCY_ID)
        logger.info(f"Using Agency ID: {agency_id} for User: {current_user.email}")
    
    # Check if agency exists
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        if current_user.role == UserRole.SUPER_ADMIN or str(agency_id) == DEFAULT_AGENCY_ID:
             # Auto-create dummy/default agency if not exists (for dev/simplicity)
            agency = Agency(id=agency_id, name="D-MIND Default Agency" if str(agency_id) == DEFAULT_AGENCY_ID else "Auto-created Agency")
            db.add(agency)
            db.commit()
            logger.info(f"Agency {agency_id} created automatically.")
        else:
            logger.error(f"Agency not found: {agency_id}")
            raise HTTPException(status_code=404, detail="Agency not found")
    
    # Create the client
    new_client = Client(
        name=client_data.name,
        industry=client_data.industry,
        agency_id=agency_id
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client

@router.get("/search", response_model=List[ClientResponse])
def search_clients(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    DEFAULT_AGENCY_ID = "00000000-0000-0000-0000-000000000000"
    agency_id = current_user.agency_id or UUID(DEFAULT_AGENCY_ID)
    
    # Simple like search
    return db.query(Client).filter(
        Client.agency_id == agency_id,
        Client.name.ilike(f"%{name}%")
    ).limit(10).all()

@router.delete("/{client_id}")
def delete_client(
    client_id: UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.models import (
        Client, PlatformConnection, Campaign, MetricsDaily, 
        SWOTAnalysis, StrategyGoal, CollaborativeTask, TaskComment,
        Report, Settlement, SettlementDetail, Lead, LeadActivity,
        LeadProfile, LeadEvent, AnalysisHistory, AnalyticsCache, SyncTask, SyncValidation
    )

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="광고주를 찾을 수 없습니다.")
    
    # 1. Permission Check
    DEFAULT_AGENCY_ID = "00000000-0000-0000-0000-000000000000"
    agency_id = current_user.agency_id or UUID(DEFAULT_AGENCY_ID)
    if current_user.role != UserRole.SUPER_ADMIN and str(client.agency_id) != str(agency_id):
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    try:
        # 2. Manual Cleanup in reverse dependency order to workaround missing DB-level cascades
        # Leads hierarchy
        lead_ids = [l.id for l in db.query(Lead).filter(Lead.client_id == client_id).all()]
        if lead_ids:
            db.query(LeadActivity).filter(LeadActivity.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(LeadProfile).filter(LeadProfile.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(LeadEvent).filter(LeadEvent.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(Lead).filter(Lead.id.in_(lead_ids)).delete(synchronize_session=False)

        # Marketing Data hierarchy
        conn_ids = [c.id for c in db.query(PlatformConnection).filter(PlatformConnection.client_id == client_id).all()]
        if conn_ids:
            camp_ids = [camp.id for camp in db.query(Campaign).filter(Campaign.connection_id.in_(conn_ids)).all()]
            if camp_ids:
                db.query(MetricsDaily).filter(MetricsDaily.campaign_id.in_(camp_ids)).delete(synchronize_session=False)
                db.query(Campaign).filter(Campaign.id.in_(camp_ids)).delete(synchronize_session=False)
            
            sync_task_ids = [s.id for s in db.query(SyncTask).filter(SyncTask.connection_id.in_(conn_ids)).all()]
            if sync_task_ids:
                db.query(SyncValidation).filter(SyncValidation.task_id.in_(sync_task_ids)).delete(synchronize_session=False)
                db.query(SyncTask).filter(SyncTask.id.in_(sync_task_ids)).delete(synchronize_session=False)
            
            db.query(PlatformConnection).filter(PlatformConnection.id.in_(conn_ids)).delete(synchronize_session=False)

        # Collaboration and Strategy
        task_ids = [t.id for t in db.query(CollaborativeTask).filter(CollaborativeTask.client_id == client_id).all()]
        if task_ids:
            db.query(TaskComment).filter(TaskComment.task_id.in_(task_ids)).delete(synchronize_session=False)
            db.query(CollaborativeTask).filter(CollaborativeTask.id.in_(task_ids)).delete(synchronize_session=False)

        settlement_ids = [s.id for s in db.query(Settlement).filter(Settlement.client_id == client_id).all()]
        if settlement_ids:
            db.query(SettlementDetail).filter(SettlementDetail.settlement_id.in_(settlement_ids)).delete(synchronize_session=False)
            db.query(Settlement).filter(Settlement.id.in_(settlement_ids)).delete(synchronize_session=False)

        # Simple relations
        db.query(SWOTAnalysis).filter(SWOTAnalysis.client_id == client_id).delete(synchronize_session=False)
        db.query(StrategyGoal).filter(StrategyGoal.client_id == client_id).delete(synchronize_session=False)
        db.query(Report).filter(Report.client_id == client_id).delete(synchronize_session=False)
        db.query(AnalysisHistory).filter(AnalysisHistory.client_id == client_id).delete(synchronize_session=False)
        db.query(AnalyticsCache).filter(AnalyticsCache.client_id == client_id).delete(synchronize_session=False)

        # 3. Finally delete the client
        db.delete(client)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"삭제 중 오류가 발생했습니다: {str(e)}")

    return {"status": "SUCCESS", "message": "광고주 정보와 모든 관련 데이터가 완전히 삭제되었습니다."}
