from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import PlatformConnection, PlatformType
from app.tasks.sync_data import sync_naver_data

router = APIRouter()

@router.get("/")
def get_connectors(db: Session = Depends(get_db)):
    """
    List available and connected platforms.
    """
    # Mock for UI demonstration
    return {
        "connectors": [
            {
                "id": "naver_ads",
                "name": "네이버 성과형 디스플레이 (GFA)",
                "category": "광고 매체",
                "status": "AVAILABLE",
                "description": "네이버 GFA 광고 성과 데이터를 실시간으로 연동하고 분석합니다."
            },
            {
                "id": "google_ads",
                "name": "Google Ads",
                "category": "광고 매체",
                "status": "AVAILABLE",
                "description": "구글 검색 및 디스플레이 광고 데이터의 성과 지표를 실시간으로 동기화합니다."
            },
            {
                "id": "meta_ads",
                "name": "Meta Ads (FB/IG)",
                "category": "광고 매체",
                "status": "AVAILABLE",
                "description": "페이스북과 인스타그램의 캠페인별 성과 Insight를 통합하여 제공합니다."
            }
        ]
    }

@router.post("/connect/{platform_id}")
def connect_platform(
    platform_id: str, 
    client_id: str, 
    credentials: dict, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    if platform_id == "naver_ads":
        platform_enum = PlatformType.NAVER_AD
    elif platform_id == "google_ads":
        platform_enum = PlatformType.GOOGLE_ADS
    elif platform_id == "meta_ads":
        platform_enum = PlatformType.META_ADS
    else:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    new_conn = PlatformConnection(
        client_id=client_id,
        platform=platform_enum,
        credentials=credentials, 
        status="ACTIVE"
    )
    db.add(new_conn)
    db.commit()
    db.refresh(new_conn)

    # Trigger initial sync
    if platform_id == "naver_ads":
        background_tasks.add_task(sync_naver_data, db, str(new_conn.id))

    return {
        "status": "SUCCESS",
        "message": f"{platform_id} 연동이 완료되었습니다.",
        "connection_id": str(new_conn.id)
    }
@router.get("/active/{client_id}")
def get_active_connections(client_id: str, db: Session = Depends(get_db)):
    """
    List active platform connections for a specific client.
    """
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.client_id == client_id,
        PlatformConnection.status == "ACTIVE"
    ).all()
    
    return [
        {
            "id": str(c.id),
            "platform": c.platform.value if hasattr(c.platform, 'value') else str(c.platform),
            "created_at": c.created_at
        } for c in connections
    ]

@router.delete("/{connection_id}")
def delete_connection(connection_id: str, db: Session = Depends(get_db)):
    """
    Delete a specific platform connection.
    """
    from uuid import UUID
    try:
        conn_uuid = UUID(connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format")
        
    connection = db.query(PlatformConnection).filter(PlatformConnection.id == conn_uuid).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    db.delete(connection)
    db.commit()
    return {"status": "SUCCESS", "message": "Connection deleted"}
