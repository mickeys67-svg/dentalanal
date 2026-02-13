import hashlib
import os
import sys

# 프로젝트의 "심장"에 해당하는 파일 목록
CRITICAL_FILES = [
    "backend/app/core/config.py",
    "backend/app/core/database.py",
    "backend/app/tasks/sync_data.py",
    "backend/app/services/naver_ads.py",
    "backend/app/services/reconciliation_service.py",
    "backend/app/services/mongo_service.py",
    "ARCHITECTURE.md",
    "backend/requirements.txt"
]

def calculate_hash(filepath):
    """파일의 SHA-256 해시를 계산합니다."""
    if not os.path.exists(filepath):
        return None
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_integrity(save_new=False):
    """파일의 무결성을 검증하거나 새로운 기준점을 저장합니다."""
    # 기준 해시 저장 파일 (프로젝트 루트)
    HASH_STORE = ".integrity_hashes"
    
    current_hashes = {}
    for f in CRITICAL_FILES:
        current_hashes[f] = calculate_hash(f)

    if save_new:
        with open(HASH_STORE, "w") as f:
            for path, h in current_hashes.items():
                if h: f.write(f"{path}:{h}\n")
        print("[Integrity] New baseline stored successfully.")
        return

    if not os.path.exists(HASH_STORE):
        print("[Integrity] No baseline hash file found. Use '--init' to create one.")
        return

    # 저장된 해시 로드
    stored_hashes = {}
    with open(HASH_STORE, "r") as f:
        for line in f:
            if ":" in line:
                path, h = line.strip().split(":", 1)
                stored_hashes[path] = h

    # 비교
    violations = []
    for path, stored_h in stored_hashes.items():
        if path not in current_hashes or current_hashes[path] != stored_h:
            violations.append(path)

    if violations:
        print("[Integrity Violation] Critical files have been modified!")
        for v in violations:
            print(f"   - {v}")
        print("\nThese files control core architecture (Supabase, MongoDB, API Reconciliation).")
        print("Use ARCHITECTURE.md for consensus before making changes.")
        # 에이전트가 이 오류를 보고 멈추게 하기 위해 0이 아닌 종료 코드 반환
        sys.exit(1)
    else:
        print("[Integrity] All critical files are protected.")

if __name__ == "__main__":
    if "--init" in sys.argv:
        check_integrity(save_new=True)
    else:
        check_integrity()
