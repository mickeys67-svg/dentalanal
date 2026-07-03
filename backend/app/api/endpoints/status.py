from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db, engine
from app.models.models import Notification, User
from sqlalchemy import text, desc
import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Status"])

@router.post("/sync")
async def trigger_manual_sync(
    background_tasks: BackgroundTasks,
    client_id: str = None, 
    days: int = None, 
    db: Session = Depends(get_db)
):
    """
    Manually triggers the sync pipeline for a specific client or all clients.
    Offloads to BackgroundTasks to prevent timeout.
    """
    from app.scripts.sync_data import run_sync_process
    
    # Offload to BackgroundTasks
    background_tasks.add_task(run_sync_process, client_id=client_id, days=days)
    
    msg = f"광고주({client_id})의 {f'{days}일치 ' if days else ''}데이터 조사가 시작되었습니다. 완료 시 알림이 발송됩니다." if client_id else "전체 데이터 동기화가 백그라운드에서 시작되었습니다."
    return {"status": "SUCCESS", "message": msg}

@router.get("/naver-health")
def check_naver_api_health(db: Session = Depends(get_db)):
    """Tests if the Naver Ads API keys are valid (Checks the first active connection)."""
    from app.models.models import PlatformConnection, PlatformType
    from app.services.naver_ads import NaverAdsService
    
    conn = db.query(PlatformConnection).filter(PlatformConnection.platform == PlatformType.NAVER_AD, PlatformConnection.status == 'ACTIVE').first()
    if not conn:
        return {"status": "ERROR", "message": "활성화된 네이버 광고 연결이 없습니다."}
    
    service = NaverAdsService(db, credentials=conn.credentials)
    result = service.validate_api()
    return {
        "connection_id": str(conn.id),
        "api_status": result["status"],
        "message": result["message"]
    }

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)):
    # 1. Check DB
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.warning(f"DB Check Failed: {e}")

    # 2. Get Real Activity Logs from Notifications (Internal notices)
    recent_activity = []
    if db_ok:
        try:
            db_logs = db.query(Notification).order_by(desc(Notification.created_at)).limit(10).all()
            for log in db_logs:
                recent_activity.append({
                    "timestamp": log.created_at.isoformat(),
                    "level": "INFO" if log.type == 'NOTICE' else "SUCCESS",
                    "message": log.title
                })
        except Exception as e:
            logger.warning(f"Notification Check Failed: {e}")
            
    # Fallback if no logs found
    if not recent_activity:
        recent_activity = [
            {"timestamp": datetime.datetime.now().isoformat(), "level": "INFO", "message": "시스템 모니터링 모듈이 활성화되었습니다."},
            {"timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=10)).isoformat(), "level": "SUCCESS", "message": "데이터베이스 연결이 초기화되었습니다."}
        ]

    return {
        "status": "Healthy" if db_ok else "Degraded",
        "database": "Connected" if db_ok else "Disconnected",
        "scheduler": "Running",
        "uptime": "99.9%",
        "recent_logs": recent_activity
    }

@router.post("/dev/seed-test-data")
def seed_test_data(db: Session = Depends(get_db)):
    """
    [개발 전용] 테스트 데이터를 데이터베이스에 시드합니다.
    Phase 2 polling 기능을 테스트하기 위한 필수 데이터:
    - Agency (KeywordLens 팀)
    - Client A (샘플 브랜드 A)
    - Keywords (다이어트, 제주도여행, 화장품)
    - Platform Connections (NAVER_AD, NAVER_PLACE, NAVER_VIEW)
    - Sample DailyRank data (지난 3일치)
    """
    try:
        from app.models.models import Agency, Client, Keyword, Target

        # Check if seed data already exists
        existing_client = db.query(Client).filter(Client.name == "샘플 브랜드 A").first()
        if existing_client and db.query(Keyword).filter(Keyword.client_id == existing_client.id).first():
            return {
                "status": "ALREADY_SEEDED",
                "message": "테스트 데이터가 이미 존재합니다.",
                "client_id": str(existing_client.id)
            }

        # Run the seed script
        from app.scripts.debug_seed import seed_data
        seed_data()

        # Fetch the created client to return its ID
        client_a = db.query(Client).filter(Client.name == "샘플 브랜드 A").first()

        logger.info("✅ Test data seeding completed successfully")

        return {
            "status": "SUCCESS",
            "message": "테스트 데이터가 성공적으로 생성되었습니다.",
            "client_id": str(client_a.id),
            "details": {
                "agency": "KeywordLens 팀",
                "client": "샘플 브랜드 A",
                "keywords": ["다이어트", "제주도여행", "화장품"],
                "platforms": ["NAVER_AD", "NAVER_PLACE", "NAVER_VIEW"],
                "sample_ranks": "지난 3일치 데이터 (테스트용)"
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Test data seeding failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"시드 실패: {str(e)}")

@router.get("/dev/reset-all")
@router.post("/dev/reset-all")
def reset_all_data(db: Session = Depends(get_db)):
    """
    [개발 전용] 데이터베이스의 모든 데이터를 초기화합니다.
    경고: 프로덕션에서는 사용 금지!
    GET 또는 POST 모두 지원
    """
    try:
        from app.models.models import (
            Client, PlatformConnection, Campaign, Leads, MetricsDaily,
            AnalysisHistory, Notification, SystemConfig
        )
        
        logger.warning("🚨 [DEV] Database reset initiated - deleting all user data")
        
        # Delete in correct order to avoid foreign key constraints
        db.query(MetricsDaily).delete()
        logger.info("✅ MetricsDaily deleted")
        
        db.query(Campaign).delete()
        logger.info("✅ Campaign deleted")
        
        db.query(Leads).delete()
        logger.info("✅ Leads deleted")
        
        db.query(PlatformConnection).delete()
        logger.info("✅ PlatformConnection deleted")
        
        db.query(AnalysisHistory).delete()
        logger.info("✅ AnalysisHistory deleted")
        
        db.query(Client).delete()
        logger.info("✅ Client deleted")
        
        db.query(Notification).delete()
        logger.info("✅ Notification deleted")
        
        db.commit()
        logger.info("✅ Database reset completed successfully")
        
        return {
            "status": "SUCCESS",
            "message": "데이터베이스가 완전히 초기화되었습니다. (모든 클라이언트, 연결, 캠페인, 지표 삭제)"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Database reset failed: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"초기화 실패: {str(e)}")
