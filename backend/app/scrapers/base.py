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

        async with async_playwright() as p:
            # Launch browser (Local or Remote)
            if cdp_url:
                self.logger.info("Connecting to Bright Data Scraping Browser...")
                browser = await p.chromium.connect_over_cdp(cdp_url)
            else:
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
                    has_touch=is_mobile
                )
                
                page = await context.new_page()

                # Bright Data might require authentication in the URL or other setup,
                # assumed handled by cdp_url (wss://user:pass@...)
                
                # Navigate
                await page.goto(url, wait_until="networkidle", timeout=60000) # Increased timeout for proxy
                
                if scroll:
                    # Scroll down to trigger lazy loading
                    for _ in range(5):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await self.random_sleep(0.5, 1.0)
                        
                else:
                    await self.random_sleep()
                    
                content = await page.content()
                return content
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {e}")
                return ""
            finally:
                if cdp_url:
                     # For CDP, we might verify if close() is fully supported or just disconnects
                     await browser.close()
                else:
                     await browser.close()
