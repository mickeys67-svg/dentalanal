#!/usr/bin/env python3
"""
Naver Maps API 테스트 - headless=False (화면에 보이게)
Naver가 headless 브라우저를 감지하는지 확인
"""

import asyncio
import urllib.parse
import json
import re
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_naver_visible():
    keyword = "서울시청"
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://map.naver.com/p/api/search/allSearch?query={encoded_keyword}&type=all&searchCoord=127.027610%3B37.498095"
    
    logger.info(f"Testing with headless=False (visible browser)...")
    logger.info(f"Keyword: {keyword}")
    logger.info(f"URL: {url[:80]}...")
    logger.info("=" * 80)
    
    async with async_playwright() as p:
        # headless=False로 실행
        logger.info("Launching VISIBLE browser (headless=False)...")
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            extra_http_headers={
                "Referer": "https://map.naver.com/",
            }
        )
        
        page = await context.new_page()
        
        logger.info("Navigating...")
        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        status = response.status if response else None
        logger.info(f"[HTTP Status] {status}")
        
        # 약간의 대기 시간 (JavaScript 실행 완료 대기)
        await asyncio.sleep(3)
        
        content = await page.content()
        logger.info(f"[Content Length] {len(content)} bytes")
        
        # HTML wrapper 제거
        if content.strip().startswith("<"):
            match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
            if match:
                content = match.group(1)
                logger.info("[HTML Wrapper] Removed")
        
        # JSON 파싱
        try:
            data = json.loads(content)
            place = data.get('result', {}).get('place')
            
            if place and isinstance(place, dict):
                place_list = place.get('list', [])
                logger.info(f"✅ SUCCESS! Found {len(place_list)} results")
                if place_list:
                    logger.info(f"First item: {place_list[0].get('name')}")
            else:
                logger.warning(f"❌ place is None/null")
                logger.info(f"Response keys: {list(data.get('result', {}).keys())}")
                
        except Exception as e:
            logger.error(f"Error: {e}")
        
        logger.info("=" * 80)
        logger.info("Browser window will stay open for 10 seconds (for debugging)...")
        await asyncio.sleep(10)
        
        await browser.close()
        logger.info("Done!")

if __name__ == "__main__":
    asyncio.run(test_naver_visible())
