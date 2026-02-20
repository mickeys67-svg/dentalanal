#!/usr/bin/env python3
"""
Naver 검색 페이지를 직접 접근하여 데이터 확인
maps.naver.com/p/api가 아니라 search.naver.com 형식 시도
"""

import asyncio
import json
import re
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_different_apis():
    """다양한 Naver API 엔드포인트 시도"""
    
    apis = [
        # 1. 기존 API (지도 API)
        {
            'name': 'Maps API (allSearch)',
            'url': 'https://map.naver.com/p/api/search/allSearch?query=서울시청&type=all&searchCoord=127.027610%3B37.498095'
        },
        # 2. 검색 API (검색 페이지)
        {
            'name': 'Search Web API',
            'url': 'https://search.naver.com/search.naver?query=서울시청&where=place'
        },
        # 3. 지도 Place API 직접
        {
            'name': 'Maps Place API',
            'url': 'https://map.naver.com/p/api/search/place?query=서울시청'
        },
        # 4. 실제 지도 페이지 방문 후 데이터 추출
        {
            'name': 'Maps Main Page',
            'url': 'https://map.naver.com/p'
        },
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for api in apis:
            logger.info("\n" + "="*80)
            logger.info(f"Testing: {api['name']}")
            logger.info(f"URL: {api['url'][:80]}...")
            logger.info("="*80)
            
            try:
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    extra_http_headers={
                        "Referer": "https://map.naver.com/",
                    }
                )
                
                page = await context.new_page()
                response = await page.goto(api['url'], wait_until="domcontentloaded", timeout=60000)
                
                status = response.status if response else None
                logger.info(f"Status: {status}")
                
                content = await page.content()
                logger.info(f"Content Length: {len(content)} bytes")
                logger.info(f"First 150 chars: {content[:150]}")
                
                # HTML wrapper 확인
                if content.strip().startswith("<"):
                    logger.warning("[HTML] Extracting from <pre>...")
                    match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
                    if match:
                        json_text = match.group(1)
                        try:
                            data = json.loads(json_text)
                            logger.info(f"✅ JSON Valid! Keys: {list(data.keys())}")
                            
                            # 데이터 확인
                            if 'result' in data:
                                result_keys = list(data['result'].keys())
                                logger.info(f"   result keys: {result_keys}")
                                
                                for key in ['place', 'address', 'bus']:
                                    val = data['result'].get(key)
                                    if val and isinstance(val, dict):
                                        list_len = len(val.get('list', []))
                                        logger.info(f"   {key}: ✅ {list_len} items")
                                    else:
                                        logger.warning(f"   {key}: ❌ null/empty")
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON Parse Failed: {e}")
                    else:
                        logger.error("Could not find <pre> tag")
                else:
                    logger.info("[JSON] Raw JSON content")
                    try:
                        data = json.loads(content)
                        logger.info(f"✅ Parsed! Keys: {list(data.keys())}")
                    except:
                        logger.error("Not valid JSON")
                
                await context.close()
                
            except Exception as e:
                logger.error(f"Error: {e}")
        
        await browser.close()
        logger.info("\n" + "="*80)
        logger.info("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_different_apis())
