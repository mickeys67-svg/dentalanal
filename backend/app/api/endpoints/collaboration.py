from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import CollaborativeTask, ApprovalRequest
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

router = APIRouter()

# --- Schemas ---

class TaskBase(BaseModel):
    title: str
    status: str = "PENDING"
    owner: Optional[str] = None
    deadline: Optional[str] = None

class TaskResponse(TaskBase):
    id: UUID
    client_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ApprovalBase(BaseModel):
    title: str
    description: Optional[str] = None
    request_type: Optional[str] = None # BUDGET, CREATIVE
    due_date: Optional[datetime] = None

class ApprovalResponse(ApprovalBase):
    id: UUID
    client_id: UUID
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/tasks/{client_id}", response_model=List[TaskResponse])
def list_tasks(client_id: UUID, db: Session = Depends(get_db)):
    return db.query(CollaborativeTask).filter(CollaborativeTask.client_id == client_id).all()

@router.post("/tasks/{client_id}", response_model=TaskResponse)
def create_task(client_id: UUID, data: TaskBase, db: Session = Depends(get_db)):
    new_task = CollaborativeTask(client_id=client_id, **data.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@router.get("/approvals/{client_id}", response_model=List[ApprovalResponse])
def list_approvals(client_id: UUID, db: Session = Depends(get_db)):
    return db.query(ApprovalRequest).filter(ApprovalRequest.client_id == client_id).all()

@router.post("/approvals/{client_id}", response_model=ApprovalResponse)
def create_approval(client_id: UUID, data: ApprovalBase, db: Session = Depends(get_db)):
    new_request = ApprovalRequest(client_id=client_id, **data.model_dump())
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.post("/approvals/{request_id}/action")
def take_approval_action(request_id: UUID, action: str, db: Session = Depends(get_db)):
    # action: APPROVED or REJECTED
    request = db.query(ApprovalRequest).filter(ApprovalRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if action not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    request.status = action
    db.commit()
    return {"status": "SUCCESS", "message": f"Request {action.lower()} completed."}
