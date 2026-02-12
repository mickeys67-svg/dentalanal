from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import CollaborativeTask, ApprovalRequest, TaskComment, User, Notification, Notice
from app.api.endpoints.auth import get_current_user
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

class CommentBase(BaseModel):
    content: str

class CommentResponse(CommentBase):
    id: UUID
    user_name: str
    created_at: datetime

    class Config:
        from_attributes = True

class NoticeBase(BaseModel):
    title: str
    content: str
    is_pinned: bool = False

class NoticeResponse(NoticeBase):
    id: UUID
    author_name: str
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
    
    # Notify? Notification Logic
    # Simplified: Create notification for the agency admin or specific owner if assigned
    # For now, let's just record it.
    
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

@router.get("/tasks/detail/{task_id}/comments", response_model=List[CommentResponse])
def get_task_comments(task_id: UUID, db: Session = Depends(get_db)):
    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc()).all()
    
    # Map to schema with user name
    results = []
    for c in comments:
        results.append({
            "id": c.id,
            "content": c.content,
            "user_name": c.user.name or c.user.email,
            "created_at": c.created_at
        })
    return results

@router.post("/tasks/detail/{task_id}/comments", response_model=CommentResponse)
def create_task_comment(
    task_id: UUID, 
    data: CommentBase, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    # Notify Task Owner (if not the commenter)
    task = db.query(CollaborativeTask).filter(CollaborativeTask.id == task_id).first()
    if task and task.owner:
        # Find user by name (simplified for demo)
        owner_user = db.query(User).filter(User.name == task.owner).first()
        if owner_user and owner_user.id != current_user.id:
            create_notification(
                db, 
                owner_user.id, 
                f"새 댓글: {task.title}", 
                f"{current_user.name or current_user.email}님이 의견을 남겼습니다.",
                link="/collaboration",
                type="COMMENT"
            )
            
    return {
        "id": new_comment.id, # Added missing id
        "content": new_comment.content, # Added missing content
        "user_name": current_user.name or current_user.email,
        "created_at": new_comment.created_at
    }

def create_notification(db: Session, user_id: UUID, title: str, content: str = None, link: str = None, type: str = None):
    notif = Notification(
        user_id=user_id,
        title=title,
        content=content,
        link=link,
        type=type
    )
    db.add(notif)
    db.commit()

@router.get("/notices", response_model=List[NoticeResponse])
def list_notices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only notices for the user's agency
    notices = db.query(Notice).filter(Notice.agency_id == current_user.agency_id).order_by(Notice.created_at.desc()).all()
    results = []
    for n in notices:
        results.append({
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "is_pinned": bool(n.is_pinned),
            "author_name": n.author.name or n.author.email,
            "created_at": n.created_at
        })
    return results

@router.post("/notices", response_model=NoticeResponse)
def create_notice(
    data: NoticeBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_notice = Notice(
        agency_id=current_user.agency_id,
        title=data.title,
        content=data.content,
        author_id=current_user.id,
        is_pinned=1 if data.is_pinned else 0
    )
    db.add(new_notice)
    db.commit()
    db.refresh(new_notice)
    
    # Notify all agency users
    agency_users = db.query(User).filter(User.agency_id == current_user.agency_id).all()
    for u in agency_users:
        if u.id != current_user.id:
            create_notification(
                db, 
                u.id, 
                f"신규 공지: {new_notice.title}", 
                "새로운 공지사항이 등록되었습니다.",
                link="/collaboration",
                type="NOTICE"
            )
            
    return {
        "id": new_notice.id,
        "title": new_notice.title,
        "content": new_notice.content,
        "is_pinned": bool(new_notice.is_pinned),
        "author_name": current_user.name or current_user.email,
        "created_at": new_notice.created_at
    }
