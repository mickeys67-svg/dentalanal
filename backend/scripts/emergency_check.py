
import asyncio
import os
import sys
from sqlalchemy import text, inspect
from datetime import datetime, timedelta

# Path setup
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from app.models.models import User, Agency, Client, MetricsDaily, Campaign, KeywordRank, ScrapeResult

def check_system_health():
    db = SessionLocal()
    print("=== [D-MIND 시스템 긴급 진단 보고서] ===")
    
    try:
        # 1. DB 연결 및 기본 정보
        print("\n1. 🏥 시스템 기본 활력 징후 (DB Connection)")
        try:
            db.execute(text("SELECT 1"))
            print("   ✅ DB 연결 성공: 정상")
        except Exception as e:
            print(f"   ❌ DB 연결 실패: {e}")
            return

        # 2. 계정 및 권한 (Auth & Hierarchy)
        print("\n2. 🔑 계정 및 권한 구조 (Auth)")
        users = db.query(User).all()
        agencies = db.query(Agency).all()
        
        print(f"   - 등록된 총 사용자 수: {len(users)}명")
        if not users:
            print("   ⚠️ [치명적] 사용자가 한 명도 없습니다. 로그인이 불가능합니다.")
        else:
            for u in users:
                print(f"     👤 [{u.role}] {u.email} (Agency: {u.agency_id})")
        
        print(f"   - 등록된 대행사(Agency) 수: {len(agencies)}개")
        if not agencies:
            print("   ⚠️ [치명적] 대행사 정보가 없습니다. 데이터 소유권이 붕괴되었습니다.")

        # 3. 데이터 흐름 (Data Pipeline)
        print("\n3. 📊 데이터 흐름 진단 (최근 24시간)")
        since = datetime.now() - timedelta(hours=48) # 넉넉히 48시간
        
        # 스크래핑 원본 데이터
        scrape_count = db.query(ScrapeResult).filter(ScrapeResult.created_at >= since).count()
        print(f"   - [수집] 최근 수집된 원본 데이터(ScrapeResult): {scrape_count} 건")
        
        # 가공된 지표 데이터
        metrics_count = db.query(MetricsDaily).filter(MetricsDaily.date >= since.date()).count()
        print(f"   - [가공] 대시보드 표시용 지표(MetricsDaily): {metrics_count} 건")
        
        if scrape_count > 0 and metrics_count == 0:
            print("   ⚠️ [진단] 수집은 되는데 대시보드용으로 '가공(ETL)'이 안 되고 있습니다. (중간 파이프라인 단절)")
        elif scrape_count == 0:
            print("   ⚠️ [진단] 수집 자체가 안 되고 있습니다. (크롤러/워커 정지)")
        else:
            print("   ✅ 데이터 흐름이 일부 감지됩니다.")

        # 4. 데이터 삭제 방해 요소 (Foreign Keys)
        print("\n4. 🗑️ 삭제 기능 차단 요소 분석")
        clients = db.query(Client).all()
        for client in clients:
            camp_cnt = db.query(Campaign).filter(Campaign.client_id == client.id).count()
            metric_cnt = db.query(MetricsDaily).filter(MetricsDaily.client_id == client.id).count()
            print(f"   - 업체 '{client.name}': 캠페인({camp_cnt}개), 지표({metric_cnt}개) 연결됨")
            if camp_cnt > 0 or metric_cnt > 0:
                print(f"     👉 이 업체를 삭제하려면 {camp_cnt + metric_cnt}개의 하위 데이터를 먼저 지워야 합니다. (Cascade 미설정 시 에러 발생)")

    except Exception as e:
        print(f"\n❌ 진단 중 알 수 없는 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n=== [진단 종료] ===")

if __name__ == "__main__":
    check_system_health()
