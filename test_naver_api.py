#!/usr/bin/env python3
"""
Naver Maps API 직접 테스트
실제 API 응답을 확인하여 근본 원인 규명
"""

import asyncio
import urllib.parse
import json
import logging
from playwright.async_api import async_playwright

# 상세 로깅 활성화
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

async def test_naver_api():
    """Naver Maps API를 직접 호출하고 응답 분석"""
    
    keyword = "임플란트"
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://map.naver.com/p/api/search/allSearch?query={encoded_keyword}&type=all&searchCoord=127.027610%3B37.498095"
    
    logger.info(f"Testing URL: {url[:100]}...")
    logger.info("=" * 80)
    
    async with async_playwright() as p:
        # 로컬 브라우저로 테스트
        logger.info("Launching local headless browser...")
        browser = await p.chromium.launch(headless=True)
        
        try:
            # Context 설정 (Referer 헤더 포함)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    "Referer": "https://map.naver.com/",
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"
                }
            )
            
            page = await context.new_page()
            
            logger.info("Navigating to Naver API...")
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000
            )
            
            # HTTP 상태 코드
            status = response.status if response else None
            logger.info(f"[HTTP Status] {status}")
            
            # 응답 헤더
            if response:
                logger.debug(f"[Response Headers] {dict(response.headers)}")
            
            # 페이지 제목
            title = await page.title()
            logger.info(f"[Page Title] {title}")
            
            # 페이지 내용
            content = await page.content()
            logger.info(f"[Content Length] {len(content)} bytes")
            logger.info(f"[First 200 chars] {content[:200]}")
            
            # [CRITICAL] HTML wrapper에서 JSON 추출
            logger.info("=" * 80)
            logger.info("Checking for HTML wrapper...")
            
            if content.strip().startswith("<"):
                logger.warning("[HTML Wrapper Detected] Extracting JSON from <pre> tag...")
                import re
                match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
                if match:
                    json_content = match.group(1)
                    logger.info(f"[JSON Extracted] Length: {len(json_content)} bytes")
                    content = json_content
                else:
                    logger.error("[HTML Parse Failed] Could not find <pre> tag")
                    return
            
            # JSON 파싱 시도
            logger.info("=" * 80)
            logger.info("Attempting JSON parsing...")
            
            try:
                data = json.loads(content)
                logger.info(f"[JSON Parsing] SUCCESS")
                logger.info(f"[Top-level keys] {list(data.keys())}")
                
                # 구조 분석
                if 'result' in data:
                    logger.info(f"[result keys] {list(data['result'].keys())}")
                    
                    if 'place' in data['result']:
                        place = data['result']['place']
                        logger.info(f"[place keys] {list(place.keys())}")
                        
                        if 'list' in place:
                            logger.info(f"[place.list length] {len(place['list'])} items")
                            if place['list']:
                                logger.info(f"[First item] {json.dumps(place['list'][0], ensure_ascii=False, indent=2)[:500]}")
                        else:
                            logger.warning(f"[WARNING] No 'list' in place object")
                    else:
                        logger.warning(f"[WARNING] No 'place' in result")
                else:
                    logger.warning(f"[WARNING] No 'result' in response")
                
                # 전체 응답 (첫 500자)
                logger.info(f"[Full Response (first 500 chars)]")
                logger.info(json.dumps(data, ensure_ascii=False)[:500])
                
            except json.JSONDecodeError as e:
                logger.error(f"[JSON Parsing FAILED] {e}")
                logger.error(f"[Response is HTML?] {content.strip().startswith('<')}")
                logger.error(f"[HTML Preview] {content[:300]}")
            
            logger.info("=" * 80)
            logger.info("Test completed!")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_naver_api())
