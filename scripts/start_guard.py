import os
import sys
import subprocess

def start_dev_session():
    """AI 에이전트가 작업을 시작하기 전 호출하는 강제 게이트웨이 스크립트"""
    print("="*60)
    print("🚀 DentalAnal AI Development Guardrail v1.0")
    print("="*60)

    # 1. ARCHITECTURE.md 존재 확인
    if not os.path.exists("ARCHITECTURE.md"):
        print("❌ [Fatal] ARCHITECTURE.md 가 유실되었습니다!")
        sys.exit(1)
    
    # 2. 무결성 검사 실행
    print("🔍 핵심 파일 무결성 검증 중...")
    try:
        # 윈도우 환경 대응: python 호출 시 절대 경로 또는 e: 드라이브 고려
        result = subprocess.run(["python", "scripts/integrity_check.py"], capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print("🚨 [Alert] 핵심 아키텍처 파일이 기준점과 다릅니다!")
            print("의도적인 수정이라면 'python scripts/integrity_check.py --init'을 먼저 실행하세요.")
            sys.exit(1)
        else:
            print("✅ 핵심 로직 무결성 확인 완료.")
    except Exception as e:
        print(f"❌ 무결성 검사 스크립트 실행 실패: {e}")

    # 3. 아키텍처 원칙 강제 출력
    print("\n💡 [기억하십시오] 핵심 아키텍처 원칙:")
    print("   - 모든 데이터: Supabase (PostgreSQL)")
    print("   - 데이터 정합성: API 우선, Scraper 백업 -> RECONCILED 생성")
    print("   - 타임존: 모든 마케팅 데이터는 KST(UTC+9) 고정")
    
    print("\n상태 확인이 완료되었습니다. 작업을 시작하세요.")
    print("="*60)

if __name__ == "__main__":
    start_dev_session()
