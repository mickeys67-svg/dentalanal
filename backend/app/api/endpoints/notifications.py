from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Notification, User
from app.api.endpoints.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

router = APIRouter()

class NotificationResponse(BaseModel):
    id: UUID
    title: str
    content: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    type: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[NotificationResponse])
@router.get("/", response_model=List[NotificationResponse], include_in_schema=False)
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    # Map is_read 0/1 to bool
    results = []
    for n in notifications:
        results.append({
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "link": n.link,
            "is_read": bool(n.is_read),
            "type": n.type,
            "created_at": n.created_at
        })
    return results

@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = 1
    db.commit()
    return {"status": "success"}

@router.post("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == 0
    ).update({"is_read": 1})
    db.commit()
    return {"status": "success"}
