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

@celery_app.task
def scrape_place_task(keyword: str):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    results = loop.run_until_complete(run_place_scraper(keyword))
    
    # Save to DB
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_place_results(keyword, results)
    finally:
        db.close()
        
    return results

@celery_app.task
def scrape_view_task(keyword: str):
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    results = loop.run_until_complete(run_view_scraper(keyword))
    
    # Save to DB
    from app.core.database import SessionLocal
    from app.services.analysis import AnalysisService
    
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        service.save_view_results(keyword, results)
    finally:
        db.close()
        
    return results
