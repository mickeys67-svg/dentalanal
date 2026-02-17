import sys
import os
import logging
from pytz import timezone

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.scheduler import start_scheduler, scheduler, KST, SYNC_HOUR, SYNC_MINUTE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestScheduler")

def test_scheduler_config():
    print(">>> Testing Scheduler Configuration...")
    
    # 1. Start Scheduler
    start_scheduler()
    
    # 2. Check Running State
    if not scheduler.running:
        print("[FAIL] Scheduler is not running!")
        return False
    print("[PASS] Scheduler started successfully.")
    
    # 3. Check Jobs
    jobs = scheduler.get_jobs()
    if not jobs:
        print("[FAIL] No jobs registered!")
        return False
    
    found_sync_job = False
    for job in jobs:
        print(f"  - Found Job: {job.id} (Trigger: {job.trigger})")
        if job.id == 'daily_marketing_sync':
            found_sync_job = True
            # Verify Trigger
            if "cron" in str(job.trigger).lower():
                print(f"[PASS] Job '{job.id}' matches Cron Trigger.")
            else:
                 print(f"[WARN] Job '{job.id}' trigger might not be cron: {job.trigger}")

    if not found_sync_job:
        print("[FAIL] 'daily_marketing_sync' job not found!")
        return False
    
    print(">>> Scheduler Verification Complete: SUCCESS")
    return True

if __name__ == "__main__":
    try:
        if test_scheduler_config():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Verification Failed: {e}")
        sys.exit(1)
    finally:
        if scheduler.running:
            scheduler.shutdown()
