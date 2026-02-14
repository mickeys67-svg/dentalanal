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
async def trigger_full_sync(background_tasks: BackgroundTasks):
    """
    Trigger full-channel data synchronization.
    """
    from app.scripts.sync_data import sync_all_channels
    background_tasks.add_task(sync_all_channels)
    return {"status": "SUCCESS", "message": "전체 채널 데이터 동기화가 시작되었습니다."}

@router.post("/cron-sync")
async def trigger_cron_sync(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Dedicated endpoint for Cloud Scheduler to trigger periodic data sync.
    """
    from datetime import datetime
    logger.info("Cron Sync triggered via Cloud Scheduler.")
    from app.scripts.sync_data import sync_all_channels
    background_tasks.add_task(sync_all_channels)
    
    return {
        "status": "ACCEPTED",
        "message": "Data synchronization routine has been dispatched to background tasks.",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/diagnostics")
def get_system_diagnostics(
    validate: bool = False,
    db: Session = Depends(get_db)
):
    """
    Diagnostic endpoint to check for data ingestion health.
    If validate=True, it performs a real network check to Naver.
    """
    from app.models.models import PlatformConnection, Campaign, MetricsDaily, Client
    from app.services.naver_ads import NaverAdsService
    from app.core.config import settings
    from datetime import datetime

    conn_count = db.query(PlatformConnection).count()
    camp_count = db.query(Campaign).count()
    client_count = db.query(Client).count()
    
    metrics_by_source = {}
    for source in ['API', 'SCRAPER', 'RECONCILED']:
        count = db.query(MetricsDaily).filter(MetricsDaily.source == source).count()
        metrics_by_source[source] = count

    import os
    db_type = "PostgreSQL" if settings.get_database_url.startswith("postgres") else "SQLite"
    is_cloud_run = os.environ.get("K_SERVICE") is not None
    
    active_naver = db.query(PlatformConnection).filter(
        PlatformConnection.platform == "NAVER_AD",
        PlatformConnection.status == "ACTIVE"
    ).all()
    
    naver_status = []
    for c in active_naver:
        creds = c.credentials or {}
        has_api = bool(creds.get('customer_id') or settings.NAVER_AD_CUSTOMER_ID)
        
        health = "UNKNOWN"
        if validate and has_api:
            # 실시간 검증 수행
            svc = NaverAdsService(db, credentials=c.credentials)
            health_res = svc.validate_api()
            health = health_res["status"]
            
        naver_status.append({
            "id": str(c.id),
            "client_id": c.client_id,
            "has_api_creds": has_api,
            "realtime_health": health
        })

    global_secrets = {
        "naver_customer_id": bool(settings.NAVER_AD_CUSTOMER_ID),
        "naver_access_license": bool(settings.NAVER_AD_ACCESS_LICENSE),
        "naver_secret_key": bool(settings.NAVER_AD_SECRET_KEY),
        "bright_data_cdp": bool(settings.BRIGHT_DATA_CDP_URL)
    }

    # Remove Celery from diagnostics if it existed
    return {
        "status": "OK",
        "environment": {
            "db_type": db_type,
            "is_cloud_run": is_cloud_run,
            "current_time_utc": datetime.utcnow().isoformat(),
            "global_secrets_configured": global_secrets
        },
        "counts": {
            "clients": client_count,
            "connections": conn_count,
            "campaigns": camp_count,
            "metrics": metrics_by_source
        },
        "naver_connections": naver_status
    }
