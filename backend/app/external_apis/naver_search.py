import httpx
import logging
from typing import List, Dict, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class NaverSearchClient:
    """
    Client for Naver Search API (Official).
    Docs: https://developers.naver.com/docs/serviceapi/search/blog/blog.md
    """
    BASE_URL = "https://openapi.naver.com/v1/search"

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or settings.NAVER_CLIENT_ID
        self.client_secret = client_secret or settings.NAVER_CLIENT_SECRET
        
        if not self.client_id or not self.client_secret:
            logger.warning("NAVER_CLIENT_ID or NAVER_CLIENT_SECRET is not set. API calls will fail.")

    @property
    def headers(self):
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

    async def search_blog(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> Dict[str, Any]:
        """
        Search for blog posts.
        :param sort: 'sim' (similarity), 'date' (date)
        """
        url = f"{self.BASE_URL}/blog.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        return await self._fetch(url, params)

    async def search_cafe(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> Dict[str, Any]:
        """
        Search for cafe articles.
        """
        url = f"{self.BASE_URL}/cafearticle.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        return await self._fetch(url, params)
    
    async def search_web(self, query: str, display: int = 10, start: int = 1, sort: str = "sim") -> Dict[str, Any]:
        """
        Search for web documents.
        """
        url = f"{self.BASE_URL}/webkr.json"
        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort
        }
        return await self._fetch(url, params)

    async def _fetch(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client_id or not self.client_secret:
            raise ValueError("Naver API credentials not configured.")
            
        import asyncio
        import random
        
        max_retries = 3
        base_delay = 1
        
        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries + 1):
                try:
                    resp = await client.get(url, headers=self.headers, params=params)
                    resp.raise_for_status()
                    return resp.json()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < max_retries:
                        # Rate Limit - Backoff
                        sleep_time = (base_delay * (2 ** attempt)) + (random.randint(0, 1000) / 1000)
                        logger.warning(f"Naver API Rate Limit (429). Retrying in {sleep_time:.2f}s... (Attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(sleep_time)
                        continue
                        
                    logger.error(f"Naver API HTTP Error: {e.response.status_code} - {e.response.text}")
                    return {"items": [], "total": 0, "error": str(e)}
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    if attempt < max_retries:
                        sleep_time = base_delay * (2 ** attempt)
                        logger.warning(f"Naver API Connection Error. Retrying in {sleep_time}s...: {e}")
                        await asyncio.sleep(sleep_time)
                        continue
                    
                    logger.error(f"Naver API Connection Error (Max Retries): {e}")
                    return {"items": [], "total": 0, "error": str(e)}
                except Exception as e:
                    logger.error(f"Naver API Unexpected Error: {e}")
                    return {"items": [], "total": 0, "error": str(e)}
