from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

class ReportTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]

class ReportTemplateCreate(ReportTemplateBase):
    agency_id: Optional[UUID] = None

class ReportTemplateResponse(ReportTemplateBase):
    id: UUID
    agency_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ReportBase(BaseModel):
    template_id: UUID
    client_id: UUID
    title: str
    status: str = "DRAFT"

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    id: UUID
    data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
