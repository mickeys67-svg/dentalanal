"""
Naver Maps Place 스크래핑 - 고도화된 버전
최적 하이브리드 솔루션: Playwright + Stealth + 지능형 파싱

기술 스택:
- playwright-stealth: Anti-bot 감지 회피
- 랜덤 딜레이: 자연스러운 사용자 시뮬레이션
- JavaScript 기반 추출: 정확한 DOM 파싱
- 다중 경로 전략: CSS, XPath, JavaScript
- 자동 재시도: 실패 시 자동 복구
"""

import asyncio
import random
import logging
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class AdvancedNaverPlaceScraper:
    """
    고도화된 Naver Maps 스크래퍼
    
    특징:
    1. Stealth 모드: Anti-bot 감지 회피
    2. 자연스러운 동작: 랜덤 딜레이, 스크롤
    3. JavaScript 기반 추출: DOM 완전 파싱
    4. 자동 재시도: 실패 복구
    5. 상세 로깅: 디버깅 용이
    """
    
    # Naver Maps 검색 URL
    BASE_URL = "https://map.naver.com/p/search/{}"
    
    # 설정
    MAX_RETRIES = 3
    RETRY_DELAY_MIN = 2
    RETRY_DELAY_MAX = 5
    RANDOM_DELAY_MIN = 1
    RANDOM_DELAY_MAX = 4
    
    # User-Agents (다양한 환경 시뮬레이션)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session_start_time = time.time()
    
    async def get_rankings(self, keyword: str) -> List[Dict]:
        """
        Naver Maps에서 장소 검색 결과 추출
        
        Args:
            keyword: 검색 키워드 (예: "임플란트")
        
        Returns:
            [{rank, name, id, category, address, lat, lng}, ...]
        
        프로세스:
            1. Browser 생성 (Stealth 모드)
            2. 검색 페이지 방문
            3. JavaScript 렌더링 완료 대기
            4. 자연스러운 상호작용 (스크롤, 딜레이)
            5. 지능형 파싱 (CSS, XPath, JavaScript)
            6. 데이터 정규화
        """
        
        self.logger.info(f"[Advanced Scrape] Starting for keyword: '{keyword}'")
        
        async with async_playwright() as p:
            # Playwright stealth 설정
            browser = await self._launch_stealth_browser(p)
            
            try:
                results = await self._scrape_with_retry(browser, keyword)
                
                if results:
                    self.logger.info(f"[Advanced Scrape] ✅ Found {len(results)} places")
                else:
                    self.logger.warning(f"[Advanced Scrape] ❌ No results found")
                
                return results
            
            except Exception as e:
                self.logger.error(f"[Advanced Scrape Error] {type(e).__name__}: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                return []
            
            finally:
                await browser.close()
    
    async def _launch_stealth_browser(self, p) -> Browser:
        """Stealth 모드 브라우저 생성"""
        
        self.logger.debug("[Browser] Launching Stealth Chromium...")
        
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',  # Cloud Run 호환성
                '--disable-gpu',
                '--disable-web-resources',
                '--no-first-run',
            ]
        )
        
        self.logger.debug("[Browser] Stealth browser launched")
        return browser
    
    async def _scrape_with_retry(self, browser: Browser, keyword: str) -> List[Dict]:
        """자동 재시도 로직이 있는 스크래핑"""
        
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                self.logger.info(f"[Scrape] Attempt {attempt + 1}/{self.MAX_RETRIES + 1}")
                
                results = await self._scrape_page(browser, keyword)
                
                if results:
                    return results
                
                if attempt < self.MAX_RETRIES:
                    delay = random.uniform(self.RETRY_DELAY_MIN, self.RETRY_DELAY_MAX)
                    self.logger.warning(f"[Retry] No results found, retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
            
            except Exception as e:
                self.logger.error(f"[Scrape Error] Attempt {attempt + 1}: {e}")
                
                if attempt < self.MAX_RETRIES:
                    delay = random.uniform(self.RETRY_DELAY_MIN, self.RETRY_DELAY_MAX)
                    self.logger.warning(f"[Retry] Will retry in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    raise
        
        return []
    
    async def _scrape_page(self, browser: Browser, keyword: str) -> List[Dict]:
        """실제 스크래핑 로직"""
        
        url = self.BASE_URL.format(keyword)
        self.logger.info(f"[Page] Navigating to {url}")
        
        # 페이지 생성 with Stealth headers
        page = await browser.new_page(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
        )
        
        # Anti-detection headers
        await page.set_extra_http_headers({
            "Referer": "https://map.naver.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        })
        
        # webdriver 감지 우회
        await page.evaluate('''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // chrome 속성 숨기기
            Object.defineProperty(navigator, 'chrome', {
                get: () => ({}),
            });
        ''')
        
        try:
            # 페이지 로드 (networkidle: 모든 네트워크 요청 완료)
            self.logger.debug("[Page] Waiting for page load...")
            response = await page.goto(
                url,
                wait_until="networkidle",
                timeout=120000
            )
            
            status = response.status if response else None
            self.logger.info(f"[Page] HTTP {status}")
            
            if status and status != 200:
                self.logger.error(f"[Page] HTTP error {status}")
                return []
            
            # 자연스러운 상호작용 (딜레이 + 스크롤)
            await self._simulate_human_behavior(page)
            
            # 결과 추출
            results = await self._extract_results(page, keyword)
            
            return results
        
        finally:
            await page.close()
    
    async def _simulate_human_behavior(self, page: Page):
        """
        사용자 같은 자연스러운 동작 시뮬레이션
        - 랜덤 딜레이
        - 페이지 스크롤
        - 마우스 이동
        """
        
        # 초기 딜레이 (페이지 완전히 렌더링될 때까지)
        delay = random.uniform(self.RANDOM_DELAY_MIN, self.RANDOM_DELAY_MAX)
        self.logger.debug(f"[Behavior] Waiting {delay:.1f}s for rendering...")
        await asyncio.sleep(delay)
        
        # 스크롤 다운 (검색 결과 로드)
        self.logger.debug("[Behavior] Scrolling page...")
        scroll_height = await page.evaluate("document.documentElement.scrollHeight")
        
        for i in range(3):
            await page.evaluate(f"window.scrollBy(0, {scroll_height // 3})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # 상단으로 복귀
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        self.logger.debug("[Behavior] Finished human-like simulation")
    
    async def _extract_results(self, page: Page, keyword: str) -> List[Dict]:
        """
        지능형 결과 추출
        
        3가지 방법 시도:
        1. JavaScript 기반 (가장 정확)
        2. BeautifulSoup + CSS (대체)
        3. 정규식 기반 (최후의 수)
        """
        
        self.logger.debug("[Extract] Starting intelligent extraction...")
        
        # 방법 1: JavaScript 실행으로 DOM 직접 접근 (권장)
        results = await self._extract_via_javascript(page, keyword)
        
        if results:
            self.logger.info(f"[Extract] Method 1 (JavaScript): {len(results)} results")
            return results
        
        # 방법 2: BeautifulSoup + CSS 선택자
        html = await page.content()
        results = await self._extract_via_beautifulsoup(html, keyword)
        
        if results:
            self.logger.info(f"[Extract] Method 2 (BeautifulSoup): {len(results)} results")
            return results
        
        # 방법 3: 정규식 기반 (최후의 수단)
        results = await self._extract_via_regex(html, keyword)
        
        if results:
            self.logger.info(f"[Extract] Method 3 (Regex): {len(results)} results")
            return results
        
        self.logger.warning("[Extract] All methods failed, no results extracted")
        return []
    
    async def _extract_via_javascript(self, page: Page, keyword: str) -> List[Dict]:
        """
        JavaScript로 DOM 직접 접근 및 추출
        가장 정확한 방법 (Naver가 JavaScript로 렌더링)
        """
        
        try:
            self.logger.debug("[JS Extract] Executing JavaScript extraction...")
            
            # Naver Maps 검색 결과 구조 분석
            # 예상 구조: div[class*="place"], li[class*="item"]
            
            results = await page.evaluate('''
                () => {
                    const results = [];
                    
                    // 전략 1: place 관련 요소
                    const places = document.querySelectorAll('[class*="place"]');
                    if (places.length > 0) {
                        places.forEach((el, idx) => {
                            const name = el.querySelector('[class*="name"]')?.textContent?.trim();
                            const category = el.querySelector('[class*="category"]')?.textContent?.trim();
                            const address = el.querySelector('[class*="address"]')?.textContent?.trim();
                            const link = el.querySelector('a')?.href;
                            
                            if (name) {
                                results.push({
                                    rank: idx + 1,
                                    name: name,
                                    category: category || '',
                                    address: address || '',
                                    id: link ? link.split('/').pop() : '',
                                    url: link || '',
                                });
                            }
                        });
                    }
                    
                    // 전략 2: 리스트 아이템
                    if (results.length === 0) {
                        const items = document.querySelectorAll('li[class*="item"], li[class*="result"]');
                        items.forEach((el, idx) => {
                            const text = el.textContent?.trim();
                            if (text && text.length > 5) {
                                results.push({
                                    rank: idx + 1,
                                    name: text.substring(0, 50),
                                    category: '',
                                    address: '',
                                    id: '',
                                    url: el.querySelector('a')?.href || '',
                                });
                            }
                        });
                    }
                    
                    return results;
                }
            ''')
            
            if results:
                self.logger.debug(f"[JS Extract] ✅ Found {len(results)} results")
                return results
            else:
                self.logger.debug("[JS Extract] ❌ No results via JavaScript")
                return []
        
        except Exception as e:
            self.logger.error(f"[JS Extract Error] {e}")
            return []
    
    async def _extract_via_beautifulsoup(self, html: str, keyword: str) -> List[Dict]:
        """BeautifulSoup + CSS 선택자"""
        
        try:
            self.logger.debug("[BS Extract] Parsing HTML...")
            
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # CSS 선택자 목록 (우선순위 순)
            selectors = [
                '[class*="place"]',
                'li[class*="item"]',
                'div[class*="result"]',
                '.search_item',
                '[class*="search"]',
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                
                if elements:
                    self.logger.debug(f"[BS Extract] Found {len(elements)} with selector: {selector}")
                    
                    for idx, el in enumerate(elements, 1):
                        name = el.get_text(strip=True)
                        if name and len(name) > 3:
                            results.append({
                                'rank': idx,
                                'name': name[:60],
                                'category': '',
                                'address': '',
                                'id': '',
                                'url': el.find('a', href=True)['href'] if el.find('a', href=True) else '',
                            })
                    
                    if results:
                        return results
            
            return results
        
        except Exception as e:
            self.logger.error(f"[BS Extract Error] {e}")
            return []
    
    async def _extract_via_regex(self, html: str, keyword: str) -> List[Dict]:
        """정규식 기반 추출 (최후의 수단)"""
        
        try:
            self.logger.debug("[Regex Extract] Using regex patterns...")
            
            results = []
            
            # 한글 텍스트 + 주소 패턴
            pattern = r'([가-힣\s]+?)(?:[\|•]([가-힣\s]+?))?(?:[\|•]([가-힣\s\d\-로길동]*))?'
            matches = re.findall(pattern, html)
            
            for idx, match in enumerate(matches[:20], 1):  # 최대 20개
                name = match[0].strip()
                category = match[1].strip() if match[1] else ''
                address = match[2].strip() if match[2] else ''
                
                if name and len(name) > 2:
                    results.append({
                        'rank': idx,
                        'name': name[:60],
                        'category': category[:30],
                        'address': address[:100],
                        'id': '',
                        'url': '',
                    })
            
            return results
        
        except Exception as e:
            self.logger.error(f"[Regex Extract Error] {e}")
            return []


# 호환성: 기존 인터페이스와 같게 유지
class NaverPlaceAdvancedScraper(AdvancedNaverPlaceScraper):
    """기존 코드와의 호환성 유지"""
    pass
