from app.core.celery_app import celery_app
from app.scrapers.naver_place import NaverPlaceScraper
from app.scrapers.naver_view import NaverViewScraper
import asyncio

async def run_place_scraper(keyword: str):
    scraper = NaverPlaceScraper()
    return await scraper.get_rankings(keyword)

async def run_view_scraper(keyword: str):
    scraper = NaverViewScraper()
    return await scraper.get_rankings(keyword)

def execute_place_sync(keyword: str):
    """Inline execution of place scraping and saving."""
    import asyncio
    import logging
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    from app.models.models import Notification, User, UserRole
    from uuid import uuid4

    logger = logging.getLogger("worker")
    
    try:
        # Use asyncio.run for a fresh loop in this thread
        results = asyncio.run(run_place_scraper(keyword))
    except Exception as e:
        logger.error(f"Scraping failed for {keyword}: {e}")
        results = []

    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_place_results(keyword, results)
        
        # Notify Admins
        admins = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).all()
        count = len(results) if results else 0
        for admin in admins:
            note = Notification(
                id=uuid4(),
                user_id=admin.id,
                title="플레이스 조사 완료",
                content=f"'{keyword}' 키워드에 대한 조사가 완료되었습니다. (수집: {count}건)",
                type="NOTICE",
                is_read=0
            )
            db.add(note)
        db.commit()
        
        logger.info(f"Place scrape finished for {keyword}. Items: {count}")
        
    except Exception as e:
        logger.error(f"Saving place results or notifying failed: {e}")
    finally:
        db.close()
    return results

def execute_view_sync(keyword: str):
    """Inline execution of view scraping and saving."""
    import asyncio
    import logging
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    from app.models.models import Notification, User, UserRole
    from uuid import uuid4
    
    logger = logging.getLogger("worker")

    try:
        results = asyncio.run(run_view_scraper(keyword))
    except Exception as e:
        logger.error(f"View scraping failed for {keyword}: {e}")
        results = []
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_view_results(keyword, results)
        
        # Notify Admins
        admins = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).all()
        count = len(results) if results else 0
        for admin in admins:
            note = Notification(
                id=uuid4(),
                user_id=admin.id,
                title="VIEW 조사 완료",
                content=f"'{keyword}' 키워드에 대한 조사가 완료되었습니다. (수집: {count}건)",
                type="NOTICE",
                is_read=0
            )
            db.add(note)
        db.commit()

        logger.info(f"View scrape finished for {keyword}. Items: {count}")
    except Exception as e:
        logger.error(f"Saving view results failed: {e}")
    finally:
        db.close()
    return results

def execute_ad_sync(keyword: str):
    """Inline execution of ad scraping and saving."""
    from app.scrapers.naver_ad import NaverAdScraper
    import asyncio
    import logging
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    from app.models.models import Notification, User, UserRole
    from uuid import uuid4
    
    logger = logging.getLogger("worker")
    scraper = NaverAdScraper()

    try:
        results = asyncio.run(scraper.get_ad_rankings(keyword))
    except Exception as e:
        logger.error(f"Ad scraping failed for {keyword}: {e}")
        results = []
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_ad_results(keyword, results)
        
        # Notify Admins
        admins = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).all()
        count = len(results) if results else 0
        for admin in admins:
            note = Notification(
                id=uuid4(),
                user_id=admin.id,
                title="광고 조사 완료",
                content=f"'{keyword}' 키워드에 대한 조사가 완료되었습니다. (수집: {count}건)",
                type="NOTICE",
                is_read=0
            )
            db.add(note)
        db.commit()

        logger.info(f"Ad scrape finished for {keyword}. Items: {count}")
    except Exception as e:
        logger.error(f"Saving ad results failed: {e}")
    finally:
        db.close()
    return results

def scrape_place_task(keyword: str):
    return execute_place_sync(keyword)

def scrape_view_task(keyword: str):
    return execute_view_sync(keyword)

def scrape_ad_task(keyword: str):
    return execute_ad_sync(keyword)
