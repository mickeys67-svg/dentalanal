#!/usr/bin/env python3
"""
Naver Maps에서 실제 네트워크 요청 캡처
브라우저 개발자 도구처럼 요청/응답 모니터링
"""

import asyncio
import json
import re
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_naver_network():
    """네이버 맵 페이지를 열고 API 요청 캡처"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 화면에 보이게
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # 네트워크 요청 모니터링
        captured_requests = []
        
        def handle_response(response):
            """API 응답 캡처"""
            url = response.url
            if 'allSearch' in url or 'search' in url:
                captured_requests.append({
                    'url': url,
                    'status': response.status,
                    'headers': dict(response.headers),
                })
                logger.info(f"\n📡 Captured: {url}")
                logger.info(f"   Status: {response.status}")
        
        page.on('response', handle_response)
        
        # 실제 네이버 맵 페이지 방문
        logger.info("Navigating to Naver Maps...")
        await page.goto("https://map.naver.com/", wait_until="networkidle", timeout=120000)
        
        # 검색 입력
        logger.info("\nSearching for '임플란트'...")
        search_input = await page.query_selector('[placeholder*="검색"]')
        if search_input:
            await search_input.fill("임플란트")
            await search_input.press("Enter")
            
            # 결과 대기
            await asyncio.sleep(3)
        
        logger.info(f"\n✅ Captured {len(captured_requests)} API requests")
        
        # 요청 목록 출력
        for i, req in enumerate(captured_requests, 1):
            logger.info(f"\n{i}. {req['url'][:100]}")
            logger.info(f"   Status: {req['status']}")
        
        # 응답 내용 직접 확인
        logger.info("\n" + "="*80)
        logger.info("Checking response body...")
        
        if captured_requests:
            # 마지막 요청의 응답 본문 확인
            page.on('response', lambda resp: logger.info(f"Response: {resp.text()}") if 'allSearch' in resp.url else None)
        
        logger.info("\n브라우저가 30초 동안 열려있습니다...")
        logger.info("개발자 도구(F12)를 사용해서 Network 탭을 확인하세요")
        
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_naver_network())
