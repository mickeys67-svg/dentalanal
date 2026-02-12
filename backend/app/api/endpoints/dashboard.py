from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.dashboard_service import DashboardService
from typing import Optional
from uuid import UUID
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def safe_uuid(id_str: Optional[str]) -> Optional[str]:
    if not id_str or id_str == "undefined" or id_str == "null":
        return None
    try:
        # Check if it's a valid UUID
        val = UUID(id_str)
        return str(val)
    except (ValueError, TypeError):
        logger.warning(f"Invalid UUID received: {id_str}")
        return None

@router.get("/summary")
def get_dashboard_summary(client_id: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"Dashboard summary requested for client_id: {client_id}")
    validated_client_id = safe_uuid(client_id)
    service = DashboardService(db)
    try:
        return service.get_summary_metrics(validated_client_id)
    except Exception as e:
        logger.error(f"Error in dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/metrics/trend")
def get_metrics_trend(client_id: Optional[str] = None, db: Session = Depends(get_db)):
    logger.info(f"Dashboard trend requested for client_id: {client_id}")
    validated_client_id = safe_uuid(client_id)
    service = DashboardService(db)
    try:
        return {"trend": service.get_trend_data(validated_client_id)}
    except Exception as e:
        logger.error(f"Error in dashboard trend: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
