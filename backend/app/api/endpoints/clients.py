from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.models import Client, Agency, User, UserRole
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel, ConfigDict
from uuid import UUID
import uuid

router = APIRouter()

class ClientBase(BaseModel):
    name: str
    industry: str
    agency_id: Optional[UUID] = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: UUID
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
    
    return db.query(Client).filter(Client.industry != None).filter(Client.agency_id == agency_id).all()

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

@router.delete("/{client_id}")
def delete_client(client_id: UUID, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
    return {"status": "SUCCESS", "message": "Client deleted"}
