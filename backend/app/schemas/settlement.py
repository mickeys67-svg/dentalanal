from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.models.models import SettlementStatus, PlatformType

class SettlementDetailBase(BaseModel):
    platform: PlatformType
    campaign_name: Optional[str] = None
    spend: float
    fee_rate: float
    fee_amount: float

class SettlementDetailCreate(SettlementDetailBase):
    pass

class SettlementDetailResponse(SettlementDetailBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SettlementBase(BaseModel):
    client_id: UUID
    period: str
    total_spend: float
    fee_amount: float
    tax_amount: float
    total_amount: float
    status: SettlementStatus
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class SettlementCreate(SettlementBase):
    pass

class SettlementUpdate(BaseModel):
    status: Optional[SettlementStatus] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None

class SettlementResponse(SettlementBase):
    id: UUID
    issued_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    details: List[SettlementDetailResponse] = []

    class Config:
        from_attributes = True
