from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_EXECUTED
import logging
from pytz import timezone

# Import the reliable sync wrapper from scripts
from app.scripts.sync_data import run_sync_process
from app.core.logger import setup_logging

# Initialize Logging
setup_logging()
logger = logging.getLogger(__name__)

# Configuration
KST = timezone('Asia/Seoul')
SYNC_HOUR = 2  # Run at 2:00 AM KST
SYNC_MINUTE = 0

scheduler = BackgroundScheduler(timezone=KST)

def job_listener(event):
    """
    Monitors job execution status.
    """
    if event.exception:
        logger.error(f"Job {event.job_id} failed: {event.exception}")
        # Future: Send alert to Slack/Email
    elif event.code == EVENT_JOB_MISSED:
        logger.warning(f"Job {event.job_id} missed schedule!")
    else:
        logger.info(f"Job {event.job_id} executed successfully.")

def start_scheduler():
    if not scheduler.running:
        # Add Listener
        scheduler.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_EXECUTED)
        
        # Add Main Sync Job
        # max_instances=1: Prevent overlap if previous job is stuck
        # coalesce=True: If missed, run only once
        scheduler.add_job(
            func=run_sync_process,
            trigger=CronTrigger(hour=SYNC_HOUR, minute=SYNC_MINUTE, timezone=KST),
            id='daily_marketing_sync',
            name='Daily Marketing Data Sync (Naver/Place/View)',
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600 # Allow 1 hour catch-up
        )
        
        scheduler.start()
        logger.info(f"Background Scheduler started. Daily Sync scheduled at {SYNC_HOUR:02d}:{SYNC_MINUTE:02d} KST.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background Scheduler stopped.")
