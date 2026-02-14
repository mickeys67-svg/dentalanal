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
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Using nest_asyncio to allow nested loops if called from sync context within async
        import nest_asyncio
        nest_asyncio.apply()
    
    results = loop.run_until_complete(run_place_scraper(keyword))
    
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_place_results(keyword, results)
    finally:
        db.close()
    return results

def execute_view_sync(keyword: str):
    """Inline execution of view scraping and saving."""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    results = loop.run_until_complete(run_view_scraper(keyword))
    
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_view_results(keyword, results)
    finally:
        db.close()
    return results

def execute_ad_sync(keyword: str):
    """Inline execution of ad scraping and saving."""
    from app.scrapers.naver_ad import NaverAdScraper
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    scraper = NaverAdScraper()
    results = loop.run_until_complete(scraper.get_ad_rankings(keyword))
    
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_ad_results(keyword, results)
    finally:
        db.close()
    return results

def scrape_place_task(keyword: str):
    return execute_place_sync(keyword)

def scrape_view_task(keyword: str):
    return execute_view_sync(keyword)

def scrape_ad_task(keyword: str):
    return execute_ad_sync(keyword)
