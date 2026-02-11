from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.settlement import SettlementResponse, SettlementUpdate
from app.services.settlement_service import SettlementService
from uuid import UUID

router = APIRouter()

from app.api.endpoints.auth import get_current_user
from app.models.models import User, UserRole

@router.post("/generate", response_model=SettlementResponse)
def generate_settlement(
    client_id: UUID,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admin or Agency Admin should generate
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
         raise HTTPException(status_code=403, detail="권한이 없습니다.")
         
    service = SettlementService(db)
    settlement = service.generate_monthly_settlement(str(client_id), year, month)
    if not settlement:
        raise HTTPException(status_code=404, detail="정산 대상 데이터를 찾을 수 없습니다.")
    return settlement

@router.get("/{client_id}", response_model=List[SettlementResponse])
def get_client_settlements(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SettlementService(db)
    return service.get_client_settlements(str(client_id))

@router.put("/{settlement_id}/status", response_model=SettlementResponse)
def update_settlement_status(
    settlement_id: UUID,
    update_data: SettlementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
    service = SettlementService(db)
    settlement = service.update_settlement_status(str(settlement_id), update_data.status, update_data.notes)
    if not settlement:
        raise HTTPException(status_code=404, detail="정산 내역을 찾을 수 없습니다.")
    return settlement
