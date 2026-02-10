from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from app.scripts.sync_data import sync_all_channels # Assuming this script exists or will be updated

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            func=sync_all_channels,
            trigger=IntervalTrigger(hours=6),
            id='sync_marketing_data',
            name='Sync all marketing channels every 6 hours',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Background Scheduler started: Syncing data every 6 hours.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background Scheduler stopped.")
