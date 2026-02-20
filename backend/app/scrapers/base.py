import asyncio
import random
import logging
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Page, BrowserContext

# Setup module-level logger
logger = logging.getLogger(__name__)

class ScraperBase:
    def __init__(self):
        self.ua_mobile = UserAgent(platforms='mobile')
        # Hardcoded Desktop UA to avoid fallback issues
        self.ua_desktop_str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_random_user_agent(self, is_mobile=True):
        return self.ua_mobile.random if is_mobile else self.ua_desktop_str

    async def random_sleep(self, min_seconds=2.5, max_seconds=5.0):
        await asyncio.sleep(random.uniform(min_seconds, max_seconds))

    async def fetch_page_content(self, url: str, scroll: bool = False, is_mobile: bool = True) -> str:
        import os
        cdp_url = os.getenv("BRIGHT_DATA_CDP_URL")
        
        # [P0 FIX] Bright Data 제거 - Naver만 지원하기로 결정
        # cdp_url을 무시하고 로컬 헤드리스 브라우저만 사용
        cdp_url = None  # Bright Data 비활성화
        
        # Sanitize env var (handle potential quotes from YAML)
        if cdp_url:
            cdp_url = cdp_url.strip().strip('"').strip("'")
            
        async with async_playwright() as p:
            # Launch browser (Local or Remote)
            if cdp_url and cdp_url.startswith("wss://"):
                self.logger.info(f"Connecting to Bright Data Scraping Browser... (URL starts with {cdp_url[:15]}...)")
                try:
                    browser = await p.chromium.connect_over_cdp(cdp_url)
                except Exception as e:
                    self.logger.error(f"Failed to connect to CDP: {e}")
                    raise e
            else:
                if cdp_url:
                    self.logger.warning(f"Invalid CDP URL format (Len: {len(cdp_url)}). Falling back to Local Browser.")
                self.logger.info("Using Local Headless Browser (No valid CDP URL found)")
                browser = await p.chromium.launch(headless=True)
            
            try:
                # Setup viewport and UA based on mobile flag
                # Note: For Bright Data, UA might be managed by the browser instance,
                # but setting context options is still good practice if supported.
                ua = await self.get_random_user_agent(is_mobile)
                viewport = {'width': 390, 'height': 844} if is_mobile else {'width': 1920, 'height': 1080}
                
                # Context with anti-bot measures
                context = await browser.new_context(
                    user_agent=ua,
                    viewport=viewport,
                    device_scale_factor=3 if is_mobile else 1,
                    is_mobile=is_mobile,
                    has_touch=is_mobile,
                    # [P0 FIX] Referer 헤더 추가 - Naver의 요청 검증을 통과하기 위함
                    extra_http_headers={
                        "Referer": "https://map.naver.com/",
                        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"
                    }
                )
                
                page = await context.new_page()

                # Bright Data might require authentication in the URL or other setup,
                # assumed handled by cdp_url (wss://user:pass@...)
                
                # Navigate with retry logic
                self.logger.info(f"Navigating to {url}...")
                max_retries = 2
                response = None
                
                for attempt in range(max_retries + 1):
                    try:
                        response = await page.goto(
                            url, 
                            wait_until="domcontentloaded", 
                            timeout=120000  # [P1 FIX] 타임아웃 60초 → 120초로 증가
                        )
                        break
                    except asyncio.TimeoutError:
                        if attempt < max_retries:
                            self.logger.warning(f"[Retry] Timeout on attempt {attempt + 1}, retrying in 2-4 seconds...")
                            await self.random_sleep(2, 4)
                        else:
                            self.logger.error(f"[Timeout] Max retries exceeded for {url}")
                            return ""
                
                # [P0 FIX] HTTP 상태 코드 로깅
                status = response.status if response else None
                self.logger.info(f"[HTTP] Status: {status}, URL: {url}")
                
                # [P0 FIX] HTTP 상태 코드 검증
                if status and status != 200:
                    self.logger.error(f"[HTTP Error] {status} for {url}")
                    return ""
                
                # Explicit wait for SPA rendering (safer than networkidle for Maps)
                await page.wait_for_timeout(5000) 
                
                title = await page.title()
                self.logger.info(f"Page loaded. Title: {title}")

                if scroll:
                    # Scroll down to trigger lazy loading
                    for _ in range(5):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await self.random_sleep(0.5, 1.0)
                        
                else:
                    await self.random_sleep()
                    
                content = await page.content()
                
                # [P0 FIX] 응답 내용 상세 로깅
                self.logger.debug(f"[Content] Length: {len(content)}, First 200 chars: {content[:200]}")
                
                # [P0 FIX] HTML vs JSON 검증
                if not content or len(content) < 10:
                    self.logger.warning(f"[Empty Response] Received {len(content)} bytes")
                    return ""
                
                if content.strip().startswith("<"):
                    self.logger.error(f"[HTML Response] Expected JSON but got HTML: {content[:100]}")
                    return ""
                
                return content
            except asyncio.TimeoutError:
                self.logger.error(f"[Timeout] page.goto() timeout for {url}")
                return ""
            except Exception as e:
                self.logger.error(f"[Error] {type(e).__name__}: {e}")
                return ""
            finally:
                if cdp_url:
                     # For CDP, we might verify if close() is fully supported or just disconnects
                     await browser.close()
                else:
                     await browser.close()
