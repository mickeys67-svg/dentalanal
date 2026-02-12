from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.naver_ads import NaverAdsService
from app.models.models import Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_all_naver_ads():
    """
    모든 클라이언트에 대해 네이버 광고 데이터를 동기화합니다.
    (실제 운영 환경에서는 스케줄러나 특정 버튼 클릭 시 트리거됨)
    """
    db = SessionLocal()
    try:
        service = NaverAdsService(db)
        clients = db.query(Client).all()
        
        if not clients:
            logger.info("동기화할 클라이언트가 없습니다.")
            return

        for client in clients:
            logger.info(f"클라이언트 '{client.name}' ({client.id}) 네이버 캠페인 동기화 시작...")
            success = service.sync_campaigns(str(client.id))
            if success:
                logger.info(f"클라이언트 '{client.name}' 동기화 성공.")
            else:
                logger.error(f"클라이언트 '{client.name}' 동기화 실패.")
                
    except Exception as e:
        logger.error(f"전체 동기화 중 오류 발생: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    sync_all_naver_ads()
