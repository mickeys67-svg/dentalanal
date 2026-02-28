from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Client, Agency, User, UserRole
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel, ConfigDict
from uuid import UUID
import uuid
import datetime
import logging

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
    conversion_value: Optional[float] = None
    fee_rate: Optional[float] = None

class ClientResponse(ClientBase):
    id: UUID
    email: Optional[str] = None
    conversion_value: Optional[float] = None  # 전환당 수익 (기본 150,000원)
    fee_rate: Optional[float] = None           # 대행 수수료율 (기본 0.15)
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
    """
    Delete a client and all related data using database CASCADE constraints.
    
    This endpoint:
    1. Verifies client exists and user has permission
    2. Deletes the client record (SQLAlchemy ORM cascade handles related records)
    3. Returns success/error with detailed error messages for debugging
    """
    from app.models.models import Client, Notification
    from sqlalchemy.exc import IntegrityError, OperationalError
    
    logger_instance = logging.getLogger(__name__)

    # 1. Fetch and validate client
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="광고주를 찾을 수 없습니다.")
    
    # 2. Permission Check
    DEFAULT_AGENCY_ID = "00000000-0000-0000-0000-000000000000"
    agency_id = current_user.agency_id or UUID(DEFAULT_AGENCY_ID)
    if current_user.role != UserRole.SUPER_ADMIN and str(client.agency_id) != str(agency_id):
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    try:
        logger_instance.info(f"[CLIENT_DELETE_START] Initiating deletion for client_id={client_id}")
        
        # 3. Delete the client record
        # SQLAlchemy CASCADE and database-level CASCADE will handle all related records
        db.delete(client)
        db.flush()  # Flush to catch constraint errors before commit
        logger_instance.info(f"[CLIENT_DELETE_FLUSH] Client record flushed to transaction, cascade deletions initiated")
        
        db.commit()
        logger_instance.info(f"[CLIENT_DELETE_SUCCESS] Client {client_id} successfully deleted with all related data")

        return {
            "status": "SUCCESS",
            "message": "광고주 정보와 모든 관련 데이터가 완전히 삭제되었습니다."
        }

    except IntegrityError as e:
        db.rollback()
        error_msg = f"Database constraint violation: {str(e.orig)}"
        logger_instance.error(f"[CLIENT_DELETE_INTEGRITY_ERROR] {error_msg}")
        
        try:
            err_notification = Notification(
                id=uuid.uuid4(),
                user_id=current_user.id,
                title="광고주 삭제 실패 - 데이터베이스 제약",
                content=f"외래키 제약 위반: 일부 데이터가 삭제되지 못했습니다. 관리자에게 문의하세요.",
                type="ERROR",
                is_read=0
            )
            db.add(err_notification)
            db.commit()
        except Exception as notify_err:
            logger_instance.warning(f"Failed to create error notification: {notify_err}")

        raise HTTPException(
            status_code=400,
            detail=f"데이터베이스 제약 조건 위반: {str(e.orig)[:100]}"
        )

    except OperationalError as e:
        db.rollback()
        error_msg = f"Database operational error: {str(e.orig)}"
        logger_instance.error(f"[CLIENT_DELETE_OPERATIONAL_ERROR] {error_msg}")

        raise HTTPException(
            status_code=500,
            detail=f"데이터베이스 오류: {str(e.orig)[:100]}"
        )

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        error_type = type(e).__name__
        logger_instance.error(f"[CLIENT_DELETE_UNKNOWN_ERROR] type={error_type}, message={error_msg}")
        
        try:
            err_notification = Notification(
                id=uuid.uuid4(),
                user_id=current_user.id,
                title="광고주 삭제 실패",
                content=f"삭제 중 오류가 발생했습니다: {error_msg[:200]}",
                type="ERROR",
                is_read=0
            )
            db.add(err_notification)
            db.commit()
        except Exception as notify_err:
            logger_instance.warning(f"Failed to create error notification: {notify_err}")

        raise HTTPException(
            status_code=500,
            detail=f"삭제 처리 중 오류: {error_msg[:100]}"
        )
