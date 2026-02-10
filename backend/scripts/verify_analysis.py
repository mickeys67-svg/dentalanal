import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.analysis import AnalysisService
from app.services.ai_service import AIService
from app.models.models import PlatformType
from app.core.database import SessionLocal

def verify_logic():
    print("--- Verifying Analysis Service Logic ---")
    db = SessionLocal()
    service = AnalysisService(db)
    
    # 1. Test calculate_sov (Check if it returns dict with expected keys)
    # Even if DB is empty, it should return 0 SOV instead of error or None
    try:
        sov_result = service.calculate_sov("송도 치과", "test_hospital", PlatformType.NAVER_PLACE)
        print(f"SOV Result: {sov_result}")
        assert "sov" in sov_result
        assert "top_rank" in sov_result
        print("✓ calculate_sov return check passed")
    except Exception as e:
        print(f"✗ calculate_sov failed: {e}")

    # 2. Test weekly_sov_summary (Import/Signature check)
    try:
        weekly = service.get_weekly_sov_summary("test_hospital", ["송도 임플란트", "송도 치과"], PlatformType.NAVER_PLACE)
        print(f"Weekly Summary Period: {weekly.get('period')}")
        print("✓ get_weekly_sov_summary check passed")
    except Exception as e:
        print(f"✗ get_weekly_sov_summary failed: {e}")

    db.close()
    
    print("\n--- Verifying AI Service Logic ---")
    ai = AIService()
    # Check if prompt extension logic works (no execution if key missing, but check method existence)
    if hasattr(ai, "generate_swot_analysis"):
        print("✓ generate_swot_analysis method exists")
    
    print("\n--- Final Verification Completed ---")

if __name__ == "__main__":
    verify_logic()
