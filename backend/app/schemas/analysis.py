from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EfficiencyItem(BaseModel):
    name: str # Campaign or Platform name
    spend: float
    conversions: int
    clicks: int
    roas: float
    cpa: float
    ctr: float
    cvr: float
    suggestion: Optional[str] = None

class EfficiencyReviewResponse(BaseModel):
    items: List[EfficiencyItem]
    overall_roas: float
    total_spend: float
    total_conversions: int
    ai_review: Optional[str] = None
    period: str
