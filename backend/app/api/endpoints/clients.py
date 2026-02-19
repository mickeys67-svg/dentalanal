from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
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

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    email: Optional[str] = None

class ClientResponse(ClientBase):
    id: UUID
    email: Optional[str] = None
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
    # Check if agency exists
    agency = db.query(Agency).filter(Agency.id == agency_id).first()
    if not agency:
        if str(agency_id) == DEFAULT_AGENCY_ID:
            # [MODIFIED] If default agency ID came in, it means user has no agency.
            # Create a NEW Agency for this user, instead of using the shared dummy one.
            new_agency_id = uuid.uuid4()
            agency_name = f"{current_user.email.split('@')[0]}의 Agency"
            
            agency = Agency(id=new_agency_id, name=agency_name)
            db.add(agency)
            
            # Update user's agency_id so next time they use this one
            current_user.agency_id = new_agency_id
            db.add(current_user)
            db.commit()
            
            # Use the new ID for client creation
            agency_id = new_agency_id
            logger.info(f"Created new Agency {agency_id} for User {current_user.email}")
        else:
            # If a specific UUID was requested but not found, that's an error (unless Super Admin auto-create logic)
            if current_user.role == UserRole.SUPER_ADMIN:
                 agency = Agency(id=agency_id, name="Auto-created Agency")
                 db.add(agency)
                 db.commit()
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

@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """클라이언트 정보 업데이트 (이메일, 이름, 업종)"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(client, field, val)

    db.commit()
    db.refresh(client)
    return client


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
        LeadProfile, LeadEvent, AnalysisHistory, AnalyticsCache, SyncTask, SyncValidation,
        ApprovalRequest
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
        logging.getLogger(__name__).info(f"Starting deletion for client {client_id}")
        
        # 2. Manual Cleanup in reverse dependency order
        # Leads hierarchy
        lead_ids = [l.id for l in db.query(Lead).filter(Lead.client_id == client_id).all()]
        if lead_ids:
            logging.getLogger(__name__).info(f"Deleting {len(lead_ids)} leads and related activities/profiles/events")
            db.query(LeadActivity).filter(LeadActivity.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(LeadProfile).filter(LeadProfile.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(LeadEvent).filter(LeadEvent.lead_id.in_(lead_ids)).delete(synchronize_session=False)
            db.query(Lead).filter(Lead.id.in_(lead_ids)).delete(synchronize_session=False)

        # Marketing Data hierarchy
        conn_ids = [c.id for c in db.query(PlatformConnection).filter(PlatformConnection.client_id == client_id).all()]
        if conn_ids:
            logging.getLogger(__name__).info(f"Deleting {len(conn_ids)} connections and related campaigns/metrics")
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
        logging.getLogger(__name__).info("Deleting tasks, comments, settlements, reports, analysis history, etc.")
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
        db.query(ApprovalRequest).filter(ApprovalRequest.client_id == client_id).delete(synchronize_session=False)

        # 2.5 Try deleting from potential orphan tables (handling schema mismatch)
        # Check information_schema to see if client_id exists before deleting, to avoid transaction errors
        potential_orphans = ["notifications", "raw_scraping_logs", "crawling_logs", "targets", "keywords"]
        for table in potential_orphans:
            try:
                # Use text() properly for the check
                check_sql = text(f"SELECT 1 FROM information_schema.columns WHERE table_name = :tname AND column_name = 'client_id'")
                result = db.execute(check_sql, {"tname": table}).scalar()
                
                if result:
                    logging.getLogger(__name__).info(f"Attempting valid cleanup for potential orphan table: {table}")
                    db.execute(text(f"DELETE FROM {table} WHERE client_id = :cid"), {"cid": str(client_id)})
            except Exception as e:
                # If checking fails, just ignore
                logging.getLogger(__name__).warning(f"Orphan cleanup check failed for {table}: {e}")
                pass

        # 3. Finally delete the client
        logging.getLogger(__name__).info("Deleting client record...")
        db.delete(client)
        db.commit()
        logging.getLogger(__name__).info("Deletion completed successfully.")

    except Exception as e:
        db.rollback()
        logging.getLogger(__name__).error(f"Client deletion failed: {e}")
        
        # Log failure to Notifications so user can see what happened
        try:
            from app.models.models import Notification
            err_note = Notification(
                id=uuid.uuid4(),
                user_id=current_user.id,
                title="광고주 삭제 실패",
                content=f"삭제 중 오류가 발생했습니다: {str(e)}",
                type="NOTICE",
                is_read=0
            )
            db.add(err_note)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to create error note: {e}")

        # Return exact error for debugging
        raise HTTPException(status_code=500, detail=f"Data Deletion Error: {str(e)}")

    return {"status": "SUCCESS", "message": "광고주 정보와 모든 관련 데이터가 완전히 삭제되었습니다."}
