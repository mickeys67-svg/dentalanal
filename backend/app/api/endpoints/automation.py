from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.services.ai_service import AIService
from app.core.database import get_db
from sqlalchemy.orm import Session
from uuid import UUID

router = APIRouter()
ai_service = AIService()

class AdCopyRequest(BaseModel):
    swot_data: Dict
    target_audience: str
    key_proposition: str

class RecommendationRequest(BaseModel):
    campaigns: List[Dict]

@router.post("/generate-copy")
def generate_copy(data: AdCopyRequest):
    """
    Generate AI ad copy based on SWOT and target info.
    """
    result = ai_service.generate_ad_copy(
        data.swot_data, 
        data.target_audience, 
        data.key_proposition
    )
    return result

@router.post("/recommendations")
def get_recommendations(data: RecommendationRequest):
    """
    Get AI-driven campaign optimization recommendations.
    """
    result = ai_service.analyze_performance_optimization(data.campaigns)
    return result

@router.post("/sync")
def trigger_full_sync(background_tasks: BackgroundTasks):
    """
    Trigger full-channel data synchronization.
    """
    from app.scripts.sync_data import sync_all_channels
    background_tasks.add_task(sync_all_channels)
    return {"status": "SUCCESS", "message": "전체 채널 데이터 동기화가 시작되었습니다."}

@router.get("/diagnostics")
def get_system_diagnostics(db: Session = Depends(get_db)):
    """
    Diagnostic endpoint to check for data ingestion health.
    """
    from app.models.models import PlatformConnection, Campaign, MetricsDaily, Client
    
    conn_count = db.query(PlatformConnection).count()
    camp_count = db.query(Campaign).count()
    client_count = db.query(Client).count()
    
    # Counts by source
    metrics_by_source = {}
    for source in ['API', 'SCRAPER', 'RECONCILED']:
        count = db.query(MetricsDaily).filter(MetricsDaily.source == source).count()
        metrics_by_source[source] = count

    # Check for potential DB environment issues
    import os
    db_type = "PostgreSQL" if settings.DATABASE_URL.startswith("postgres") else "SQLite"
    is_cloud_run = os.environ.get("K_SERVICE") is not None
    
    # Check if we have any active Naver connections with credentials
    active_naver = db.query(PlatformConnection).filter(
        PlatformConnection.platform == "NAVER_AD",
        PlatformConnection.status == "ACTIVE"
    ).all()
    
    naver_status = []
    for c in active_naver:
        creds = c.credentials or {}
        has_api = bool(creds.get('customer_id') and (creds.get('api_key') or creds.get('access_license')))
        has_scraper = bool(creds.get('username') and creds.get('password'))
        naver_status.append({
            "id": str(c.id),
            "client_id": c.client_id,
            "has_api_creds": has_api,
            "has_scraper_creds": has_scraper
        })

    # Check global settings (Environment Variables)
    global_settings = {
        "naver_customer_id": bool(settings.NAVER_AD_CUSTOMER_ID),
        "naver_access_license": bool(settings.NAVER_AD_ACCESS_LICENSE),
        "naver_secret_key": bool(settings.NAVER_AD_SECRET_KEY),
        "bright_data_cdp": bool(settings.BRIGHT_DATA_CDP_URL)
    }

    return {
        "status": "OK",
        "environment": {
            "db_type": db_type,
            "is_cloud_run": is_cloud_run,
            "current_time_utc": datetime.utcnow().isoformat(),
            "global_secrets_configured": global_settings
        },
        "counts": {
            "clients": client_count,
            "connections": conn_count,
            "campaigns": camp_count,
            "metrics": metrics_by_source
        },
        "naver_connections": naver_status
    }
