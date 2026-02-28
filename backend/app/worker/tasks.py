"""
Scraping Tasks - 완전 async 버전

asyncio.run() 완전 제거 → FastAPI BackgroundTasks와 호환.
Playwright 의존성 없음 - httpx 기반 스크래퍼 직접 사용.
"""
import logging
from uuid import UUID, uuid4

logger = logging.getLogger("worker")


# ────────────────────────────────────────────────────────────
# 공통 DB 저장 + 알림 처리
# ────────────────────────────────────────────────────────────

def _save_and_notify(keyword: str, results: list, client_uuid, platform_label: str,
                     save_fn, error_msg: str = None):
    """스크래핑 결과 DB 저장 + 관리자 알림 (동기 함수, SessionLocal 사용)."""
    from app.core.database import SessionLocal
    from app.models.models import Notification, User, UserRole

    count = len(results)
    db = SessionLocal()
    try:
        save_fn(db, keyword, results, client_uuid)

        # 관리자 알림
        if error_msg:
            title = f"{platform_label} 조사 실패"
            content = f"'{keyword}' 키워드 오류: {error_msg}"
        elif count == 0:
            title = f"{platform_label} 조사 결과 없음"
            content = f"'{keyword}' - 데이터 0건"
        else:
            title = f"{platform_label} 조사 완료"
            content = f"'{keyword}' 완료 ({count}건 수집)"

        admins = db.query(User).filter(
            User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN])
        ).all()
        for admin in admins:
            db.add(Notification(
                id=uuid4(),
                user_id=admin.id,
                title=title,
                content=content,
                type="NOTICE",
                is_read=0,
            ))
        db.commit()
        logger.info(f"[{platform_label}] '{keyword}' 저장 완료 ({count}건)")
    except Exception as e:
        logger.error(f"[{platform_label}] DB 저장 실패: {e}")
        db.rollback()
    finally:
        db.close()


# ────────────────────────────────────────────────────────────
# Place 저장 함수 (동기)
# ────────────────────────────────────────────────────────────

def _save_place(db, keyword, results, client_uuid):
    from app.services.analysis import AnalysisService
    if results:
        AnalysisService(db).save_place_results(keyword, results, client_uuid)


def _save_view(db, keyword, results, client_uuid):
    from app.services.analysis import AnalysisService
    if results:
        AnalysisService(db).save_view_results(keyword, results, client_uuid)


def _save_ad(db, keyword, results, client_uuid):
    from app.services.analysis import AnalysisService
    if results:
        AnalysisService(db).save_ad_results(keyword, results, client_uuid)


# ────────────────────────────────────────────────────────────
# async Task 함수들 (FastAPI BackgroundTasks에서 직접 await)
# ────────────────────────────────────────────────────────────

async def scrape_place_task(keyword: str, client_id: str = None):
    """네이버 플레이스 스크래핑 - httpx 직접 호출, asyncio.run() 없음."""
    from app.scrapers.naver_place import NaverPlaceScraper

    client_uuid = UUID(client_id) if client_id else None
    results = []
    error_msg = None

    try:
        scraper = NaverPlaceScraper()
        results = await scraper.get_rankings(keyword)
    except Exception as e:
        import traceback
        error_msg = str(e)
        logger.error(f"[Place] '{keyword}' 스크래핑 실패: {type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except Exception:
            pass

    _save_and_notify(keyword, results, client_uuid, "플레이스", _save_place, error_msg)
    return results


async def scrape_view_task(keyword: str, client_id: str = None):
    """네이버 VIEW 스크래핑 - httpx HTML 파싱, asyncio.run() 없음."""
    from app.scrapers.naver_view import NaverViewScraper

    client_uuid = UUID(client_id) if client_id else None
    results = []
    error_msg = None

    try:
        scraper = NaverViewScraper()
        results = await scraper.get_rankings(keyword)
    except Exception as e:
        import traceback
        error_msg = str(e)
        logger.error(f"[View] '{keyword}' 스크래핑 실패: {type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except Exception:
            pass

    _save_and_notify(keyword, results, client_uuid, "VIEW", _save_view, error_msg)
    return results


async def scrape_ad_task(keyword: str, client_id: str = None):
    """네이버 광고 순위 스크래핑 - httpx, asyncio.run() 없음."""
    from app.scrapers.naver_ad import NaverAdScraper

    client_uuid = UUID(client_id) if client_id else None
    results = []
    error_msg = None

    try:
        scraper = NaverAdScraper()
        results = await scraper.get_ad_rankings(keyword)
    except Exception as e:
        import traceback
        error_msg = str(e)
        logger.error(f"[Ad] '{keyword}' 스크래핑 실패: {type(e).__name__}: {e}")
        logger.debug(traceback.format_exc())
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(e)
        except Exception:
            pass

    _save_and_notify(keyword, results, client_uuid, "광고", _save_ad, error_msg)
    return results


# ────────────────────────────────────────────────────────────
# 스케줄러 호환용 sync wrapper (scheduler.py에서 호출)
# ────────────────────────────────────────────────────────────

def run_place_scraper_sync(keyword: str, client_id: str = None):
    """스케줄러(BackgroundScheduler)에서 호출용 - 별도 이벤트 루프에서 실행."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(scrape_place_task(keyword, client_id))
    finally:
        loop.close()


def run_view_scraper_sync(keyword: str, client_id: str = None):
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(scrape_view_task(keyword, client_id))
    finally:
        loop.close()


# 하위호환성 - sync_data.py 등에서 사용
async def run_place_scraper(keyword: str):
    from app.scrapers.naver_place import NaverPlaceScraper
    return await NaverPlaceScraper().get_rankings(keyword)


async def run_view_scraper(keyword: str):
    from app.scrapers.naver_view import NaverViewScraper
    return await NaverViewScraper().get_rankings(keyword)
