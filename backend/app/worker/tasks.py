from app.core.celery_app import celery_app
from app.scrapers.naver_place import NaverPlaceScraper
from app.scrapers.naver_view import NaverViewScraper
from app.scrapers.safe_wrapper import SafeScraperWrapper
from app.schemas.response import ResponseStatus
import asyncio
import logging

logger = logging.getLogger("worker")

async def run_place_scraper(keyword: str):
    scraper = NaverPlaceScraper()
    wrapper = SafeScraperWrapper(scraper)
    response = await wrapper.run("get_rankings", keyword)
    
    if response.status == ResponseStatus.SUCCESS and response.data:
        return response.data
    # On failure, SafeWrapper has already logged to Sentry.
    # We return empty list to maintain compatibility with existing DB logic.
    return []

async def run_view_scraper(keyword: str):
    scraper = NaverViewScraper()
    wrapper = SafeScraperWrapper(scraper)
    response = await wrapper.run("get_rankings", keyword)
    
    if response.status == ResponseStatus.SUCCESS and response.data:
        return response.data
    return []

def execute_place_sync(keyword: str, client_id_str: str = None):
    """Inline execution of place scraping and saving."""
    import asyncio
    import logging
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    from app.models.models import Notification, User, UserRole
    from uuid import UUID, uuid4

    logger = logging.getLogger("worker")
    error_msg = None
    
    # Convert string ID to UUID safely
    client_uuid = UUID(client_id_str) if client_id_str else None
    
    try:
        # Use asyncio.run for a fresh loop in this thread
        results = asyncio.run(run_place_scraper(keyword))
    except Exception as e:
        logger.error(f"Scraping failed for {keyword}: {e}")
        error_msg = str(e)
        results = []

    db = SessionLocal()
    try:
        service = AnalysisService(db)
        if results:
            service.save_place_results(keyword, results, client_uuid)
        
        # Notify Admins
        admins = db.query(User).filter(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])).all()
        count = len(results) if results else 0
        
        if error_msg:
            title = "플레이스 조사 실패"
            content = f"'{keyword}' 키워드 조사 중 오류가 발생했습니다: {error_msg}"
        elif count == 0:
             title = "플레이스 조사 결과 없음"
             content = f"'{keyword}' 키워드에 대한 데이터가 발견되지 않았습니다. (0건)"
        else:
            title = "플레이스 조사 완료"
            content = f"'{keyword}' 키워드에 대한 조사가 완료되었습니다. (수집: {count}건)"

        for admin in admins:
            note = Notification(
                id=uuid4(),
                user_id=admin.id,
                title=title,
                content=content,
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

def execute_view_sync(keyword: str, client_id_str: str = None):
    """Inline execution of view scraping and saving."""
    import asyncio
    import logging
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    from app.models.models import Notification, User, UserRole
    from uuid import UUID, uuid4
    
    logger = logging.getLogger("worker")
    error_msg = None
    
    client_uuid = UUID(client_id_str) if client_id_str else None

    try:
        results = asyncio.run(run_view_scraper(keyword))
    except Exception as e:
        logger.error(f"View scraping failed for {keyword}: {e}")
        error_msg = str(e)
        results = []
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        if results:
            service.save_view_results(keyword, results, client_uuid)
        
        # Notify Admins
        admins = db.query(User).filter(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])).all()
        count = len(results) if results else 0
        
        if error_msg:
            title = "VIEW 조사 실패"
            content = f"'{keyword}' 키워드 조사 중 오류가 발생했습니다: {error_msg}"
        elif count == 0:
             title = "VIEW 조사 결과 없음"
             content = f"'{keyword}' 키워드에 대한 데이터가 발견되지 않았습니다. (0건)"
        else:
            title = "VIEW 조사 완료"
            content = f"'{keyword}' 키워드에 대한 조사가 완료되었습니다. (수집: {count}건)"

        for admin in admins:
            note = Notification(
                id=uuid4(),
                user_id=admin.id,
                title=title,
                content=content,
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

def execute_ad_sync(keyword: str, client_id_str: str = None):
    """Inline execution of ad scraping and saving."""
    from app.scrapers.naver_ad import NaverAdScraper
    import asyncio
    import logging
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    from app.models.models import Notification, User, UserRole
    from uuid import UUID, uuid4
    
    logger = logging.getLogger("worker")
    scraper = NaverAdScraper()
    wrapper = SafeScraperWrapper(scraper)
    error_msg = None
    
    client_uuid = UUID(client_id_str) if client_id_str else None

    try:
        response = asyncio.run(wrapper.run("get_ad_rankings", keyword))
        if response.status == ResponseStatus.SUCCESS and response.data:
            results = response.data
        else:
            results = []
            if response.message:
                error_msg = response.message # Capture wrapper error message if any
    except Exception as e:
        logger.error(f"Ad scraping failed for {keyword}: {e}")
        error_msg = str(e)
        results = []
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        if results:
            service.save_ad_results(keyword, results, client_uuid)
        
        # Notify Admins
        admins = db.query(User).filter(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])).all()
        count = len(results) if results else 0
        
        if error_msg:
            title = "광고 조사 실패"
            content = f"'{keyword}' 키워드 조사 중 오류가 발생했습니다: {error_msg}"
        elif count == 0:
             title = "광고 조사 결과 없음"
             content = f"'{keyword}' 키워드에 대한 데이터가 발견되지 않았습니다. (0건)"
        else:
            title = "광고 조사 완료"
            content = f"'{keyword}' 키워드에 대한 조사가 완료되었습니다. (수집: {count}건)"

        for admin in admins:
            note = Notification(
                id=uuid4(),
                user_id=admin.id,
                title=title,
                content=content,
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

def scrape_place_task(keyword: str, client_id: str = None):
    return execute_place_sync(keyword, client_id)

def scrape_view_task(keyword: str, client_id: str = None):
    return execute_view_sync(keyword, client_id)

def scrape_ad_task(keyword: str, client_id: str = None):
    return execute_ad_sync(keyword, client_id)
