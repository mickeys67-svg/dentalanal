
import logging
import time
import asyncio
from typing import Any, Callable, Dict, Optional, TypeVar
from functools import wraps
from datetime import datetime

# Safe imports
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

from app.schemas.response import APIResponse, ResponseStatus

logger = logging.getLogger(__name__)

T = TypeVar("T")

class SafeScraperWrapper:
    """
    A robust wrapper for any scraper class or function.
    Handles:
    1. Error Capture (Sentry + Logging)
    2. Response Standardization (APIResponse envelope)
    3. Performance Timing
    """
    
    def __init__(self, scraper_instance: Any = None):
        self.scraper = scraper_instance

    async def run(self, method_name: str, *args, **kwargs) -> APIResponse:
        """
        Execute a method on the scraper instance safely.
        """
        start_time = time.time()
        meta = {
            "method": method_name,
            "args": str(args), 
            "kwargs": str(kwargs),
            "timestamp": datetime.now().isoformat()
        }

        try:
            if not self.scraper:
                raise ValueError("Scraper instance not provided")

            method = getattr(self.scraper, method_name, None)
            if not method:
                raise AttributeError(f"Method '{method_name}' not found on scraper")

            # Execute the actual scraping logic
            result = await method(*args, **kwargs)

            # Calculate duration
            duration = time.time() - start_time
            meta["duration_seconds"] = round(duration, 3)

            # If result is empty list or None, consider it a potential issue (PARTIAL_SUCCESS)
            # but still return as SUCCESS for now, just empty
            if result is None:
                result = []
            
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                data=result,
                message="Scraping completed successfully",
                meta=meta
            )

        except Exception as e:
            duration = time.time() - start_time
            meta["duration_seconds"] = round(duration, 3)
            meta["error_type"] = type(e).__name__
            
            error_msg = str(e)
            logger.error(f"❌ Scraping Failed [{method_name}]: {error_msg}", exc_info=True)

            # Send to Sentry
            if sentry_sdk:
                with sentry_sdk.push_scope() as scope:
                    scope.set_extra("scraping_meta", meta)
                    sentry_sdk.capture_exception(e)

            return APIResponse(
                status=ResponseStatus.ERROR,
                message=f"Scraping failed: {error_msg}",
                meta=meta
            )

# Decorator for standalone functions if needed
def safe_scrape(func: Callable[..., Any]):
    @wraps(func)
    async def wrapper(*args, **kwargs) -> APIResponse:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return APIResponse(
                status=ResponseStatus.SUCCESS,
                data=result,
                meta={"duration": time.time() - start_time}
            )
        except Exception as e:
            if sentry_sdk:
                sentry_sdk.capture_exception(e)
            return APIResponse(
                status=ResponseStatus.ERROR,
                message=str(e)
            )
    return wrapper
