from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import SWOTAnalysis, StrategyGoal
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

router = APIRouter()

# --- Schemas ---

class SWOTBase(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]

class SWOTResponse(SWOTBase):
    id: UUID
    client_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True

class GoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    smart_s: Optional[str] = None
    smart_m: Optional[str] = None
    smart_a: Optional[str] = None
    smart_r: Optional[str] = None
    smart_t: Optional[str] = None
    status: str = "IN_PROGRESS"

class GoalResponse(GoalBase):
    id: UUID
    client_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("/swot/{client_id}", response_model=SWOTResponse)
def get_swot(client_id: UUID, db: Session = Depends(get_db)):
    swot = db.query(SWOTAnalysis).filter(SWOTAnalysis.client_id == client_id).first()
    if not swot:
        # Return empty SWOT if not found
        return {
            "id": client_id, # Placeholder
            "client_id": client_id,
            "strengths": [], "weaknesses": [], "opportunities": [], "threats": [],
            "updated_at": datetime.now()
        }
    return swot

@router.post("/swot/{client_id}", response_model=SWOTResponse)
def save_swot(client_id: UUID, data: SWOTBase, db: Session = Depends(get_db)):
    swot = db.query(SWOTAnalysis).filter(SWOTAnalysis.client_id == client_id).first()
    if not swot:
        swot = SWOTAnalysis(client_id=client_id, **data.dict())
        db.add(swot)
    else:
        for key, value in data.dict().items():
            setattr(swot, key, value)
    db.commit()
    db.refresh(swot)
    return swot

@router.get("/goals/{client_id}", response_model=List[GoalResponse])
def list_goals(client_id: UUID, db: Session = Depends(get_db)):
    return db.query(StrategyGoal).filter(StrategyGoal.client_id == client_id).all()

@router.post("/goals/{client_id}", response_model=GoalResponse)
def create_goal(client_id: UUID, data: GoalBase, db: Session = Depends(get_db)):
    new_goal = StrategyGoal(client_id=client_id, **data.dict())
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal

class SimulationRequest(BaseModel):
    budget: float
    target_roas: float

@router.post("/simulate-budget")
def simulate_budget(data: SimulationRequest):
    # Simple ROI-based simulation logic
    # In a real scenario, this would use historical metrics to build a curve
    estimated_conversions = (data.budget * (data.target_roas / 100)) / 50000 # Assuming 50k revenue per conversion
    estimated_revenue = data.budget * (data.target_roas / 100)
    
    return {
        "budget": data.budget,
        "target_roas": data.target_roas,
        "estimated_conversions": round(estimated_conversions, 1),
        "estimated_revenue": round(estimated_revenue, 0),
        "confidence_score": 0.85
    }
