from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/summary")
def get_dashboard_summary(client_id: str = None, db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_summary_metrics(client_id)

@router.get("/metrics/trend")
def get_metrics_trend(client_id: str = None, db: Session = Depends(get_db)):
    service = DashboardService(db)
    return {"trend": service.get_trend_data(client_id)}
