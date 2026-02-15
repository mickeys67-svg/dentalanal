from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from app.scripts.sync_data import sync_all_channels # Assuming this script exists or will be updated

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def sync_wrapper():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sync_all_channels())
    loop.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            func=sync_wrapper,
            trigger=IntervalTrigger(hours=6),
            id='sync_marketing_data',
            name='Sync all marketing channels every 6 hours',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Background Scheduler started: Sync scheduled every 6 hours.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background Scheduler stopped.")
