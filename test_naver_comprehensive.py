#!/usr/bin/env python3
"""
여러 키워드로 Naver Maps API 테스트
어떤 키워드가 데이터를 반환하는지 확인
"""

import asyncio
import urllib.parse
import json
import logging
import re
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def test_keyword(keyword: str):
    """단일 키워드 테스트"""
    
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://map.naver.com/p/api/search/allSearch?query={encoded_keyword}&type=all&searchCoord=127.027610%3B37.498095"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    "Referer": "https://map.naver.com/",
                    "Accept-Language": "ko-KR,ko;q=0.9"
                }
            )
            
            page = await context.new_page()
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            content = await page.content()
            
            # HTML wrapper 제거
            if content.strip().startswith("<"):
                match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
                if match:
                    content = match.group(1)
            
            # JSON 파싱
            data = json.loads(content)
            
            # 결과 분석
            result_keys = list(data.get('result', {}).keys())
            place_data = data.get('result', {}).get('place')
            
            if place_data and isinstance(place_data, dict):
                place_list = place_data.get('list', [])
                place_count = len(place_list) if place_list else 0
                logger.info(f"✅ [{keyword}] FOUND {place_count} results | result keys: {result_keys}")
                if place_count > 0:
                    logger.info(f"   First item: {place_list[0].get('name', 'N/A')} | {place_list[0].get('category', 'N/A')}")
            else:
                logger.warning(f"❌ [{keyword}] NO DATA (place={place_data}) | result keys: {result_keys}")
                # 다른 카테고리 확인
                address = data.get('result', {}).get('address')
                bus = data.get('result', {}).get('bus')
                if address or bus:
                    logger.info(f"   But found: address={address is not None}, bus={bus is not None}")
            
            await context.close()
            
        except Exception as e:
            logger.error(f"❌ [{keyword}] ERROR: {e}")
        finally:
            await browser.close()

async def main():
    """여러 키워드 테스트"""
    
    keywords = [
        "임플란트",           # 원래 키워드
        "치과",               # 더 일반적인 키워드
        "강남역 치과",        # 지역 포함
        "서울 임플란트",      # 지역 포함
        "배재대학교",         # 알려진 장소 (대학교)
        "서울시청",           # 알려진 장소 (건물)
    ]
    
    logger.info("=" * 80)
    logger.info("Testing multiple keywords with Naver Maps API")
    logger.info("=" * 80)
    
    for keyword in keywords:
        await test_keyword(keyword)
        await asyncio.sleep(1)  # Rate limit
    
    logger.info("=" * 80)
    logger.info("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
