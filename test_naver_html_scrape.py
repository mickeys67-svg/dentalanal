#!/usr/bin/env python3
"""
Naver Maps 검색 결과 HTML에서 직접 데이터 추출
API가 작동하지 않으므로 웹 페이지 스크래핑으로 전환
"""

import asyncio
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_naver_html_scrape():
    """Naver Maps 페이지에서 HTML 스크래핑"""
    
    keyword = "서울시청"
    
    async with async_playwright() as p:
        logger.info(f"🔍 Testing HTML scraping for '{keyword}'")
        logger.info("="*80)
        
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # 방법 1: 지도 검색 페이지
        search_url = f"https://map.naver.com/p/search/{keyword}"
        logger.info(f"Method 1: Visiting {search_url}")
        
        response = await page.goto(search_url, wait_until="networkidle", timeout=120000)
        status = response.status if response else None
        logger.info(f"Status: {status}")
        
        # HTML 분석
        html = await page.content()
        logger.info(f"HTML Length: {len(html)} bytes")
        
        # BeautifulSoup로 파싱
        soup = BeautifulSoup(html, 'html.parser')
        
        # 검색 결과 찾기 (다양한 selector 시도)
        selectors = [
            'a.place_name',
            '.place_item',
            '[class*="place"]',
            '[class*="search_result"]',
            '.searchLocation_item',
        ]
        
        logger.info("\n🔎 Searching for place results...")
        
        found_any = False
        for selector in selectors:
            results = soup.select(selector)
            if results:
                found_any = True
                logger.info(f"\n✅ Found {len(results)} items with selector: {selector}")
                
                for i, item in enumerate(results[:3], 1):
                    logger.info(f"\n   Item {i}:")
                    logger.info(f"   Text: {item.get_text(strip=True)[:60]}")
                    logger.info(f"   HTML: {str(item)[:200]}")
        
        if not found_any:
            logger.warning("No results found with common selectors")
            
            # 전체 HTML 구조 분석
            logger.info("\n📋 HTML Structure Analysis:")
            
            # JavaScript로 렌더링된 데이터 찾기
            scripts = soup.find_all('script')
            logger.info(f"   Found {len(scripts)} script tags")
            
            for script in scripts[:3]:
                text = script.string
                if text and len(text) > 50:
                    logger.info(f"   Script preview: {text[:150]}")
        
        # 방법 2: 모바일 버전 시도
        logger.info("\n" + "="*80)
        logger.info("Method 2: Testing mobile version")
        
        # 모바일 유저에이전트로 재시도
        mobile_context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            viewport={'width': 390, 'height': 844}
        )
        mobile_page = await mobile_context.new_page()
        
        response = await mobile_page.goto(search_url, wait_until="networkidle", timeout=120000)
        status = response.status if response else None
        logger.info(f"Status: {status}")
        
        html = await mobile_page.content()
        logger.info(f"HTML Length: {len(html)} bytes")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 모바일에서 찾기
        place_items = soup.find_all('div', class_=lambda x: x and 'place' in x.lower())
        if place_items:
            logger.info(f"✅ Found {len(place_items)} place items on mobile")
            for item in place_items[:2]:
                logger.info(f"   {item.get_text(strip=True)[:80]}")
        else:
            logger.warning("No place items found on mobile either")
        
        await browser.close()
        
        logger.info("\n" + "="*80)
        logger.info("Analysis complete")

if __name__ == "__main__":
    asyncio.run(test_naver_html_scrape())
