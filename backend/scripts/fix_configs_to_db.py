import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import engine, Base
from app.models.models import SystemConfig
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

def init_system_configs():
    print("--- SystemConfig 테이블 생성 및 데이터 동기화 시작 ---")
    
    # 1. 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("[OK] `system_configs` 테이블이 생성/확인되었습니다.")
    
    # 2. 현재 .env 에서 값 가져와서 저장 (값이 있을 때만)
    load_dotenv()
    db = Session(bind=engine)
    
    important_keys = [
        "NAVER_AD_CUSTOMER_ID",
        "NAVER_AD_ACCESS_LICENSE",
        "NAVER_AD_SECRET_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
        "BRIGHT_DATA_CDP_URL",
        "DATABASE_URL",
        "MONGODB_URL"
    ]
    
    for key in important_keys:
        val = os.getenv(key)
        if val:
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                config = SystemConfig(key=key, value=val, description="Auto-saved from .env/Secrets")
                db.add(config)
                print(f"[SAVED] {key} 정보가 DB에 영구 저장되었습니다.")
            else:
                existing.value = val
                print(f"[UPDATED] {key} 정보가 최신화되었습니다.")
    
    db.commit()
    db.close()
    print("--- 설정 고정 작업 완료 ---")

if __name__ == "__main__":
    init_system_configs()
