from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.models import User, UserRole
from app.core.security import get_password_hash
from pydantic import BaseModel, EmailStr
from uuid import UUID

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    birth_date: Optional[str] = None
    agency_id: Optional[UUID] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None
    role: UserRole
    is_active: int
    birth_date: Optional[str] = None
    agency_id: Optional[UUID] = None

    class Config:
        from_attributes = True

from app.api.endpoints.auth import get_current_user, get_optional_current_user

@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return db.query(User).all()

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    # If no users exist, allow creating the first admin
    num_users = db.query(User).count()
    
    if num_users > 0:
        if not current_user:
            raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        name=user_in.name,
        role=user_in.role,
        birth_date=user_in.birth_date,
        agency_id=user_in.agency_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.delete("/{user_id}")
def delete_user(
    user_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
