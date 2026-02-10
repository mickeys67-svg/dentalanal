from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.models import Client, Agency
from pydantic import BaseModel, ConfigDict
from uuid import UUID
import uuid

router = APIRouter()

class ClientBase(BaseModel):
    name: str
    industry: str
    agency_id: UUID

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client_data: ClientCreate, db: Session = Depends(get_db)):
    # Check if agency exists, if not create a default one for now
    agency = db.query(Agency).filter(Agency.id == client_data.agency_id).first()
    if not agency:
        # For simplicity in this demo/initial phase, we'll auto-create an agency if it doesn't exist
        # Better to have a separate agency management but this unblocks client creation
        agency = Agency(id=client_data.agency_id, name="Default Agency")
        db.add(agency)
        db.commit()
    
    new_client = Client(**client_data.model_dump())
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
