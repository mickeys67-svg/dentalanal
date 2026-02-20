"""
Naver Maps Place 스크래핑 - HTML 기반
API가 작동하지 않으므로 웹 페이지를 직접 스크래핑

공식 API 대신 검색 결과 페이지 HTML에서 데이터 추출
"""

import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from app.scrapers.base import ScraperBase

logger = logging.getLogger(__name__)


class NaverPlaceHtmlScraper(ScraperBase):
    """Naver Maps 검색 결과를 HTML에서 직접 추출"""
    
    # Naver Maps 검색 페이지
    BASE_URL = "https://map.naver.com/p/search/{}"
    
    async def get_rankings(self, keyword: str) -> List[Dict]:
        """
        Naver Maps에서 장소 검색 결과 추출
        
        Args:
            keyword: 검색 키워드 (예: "임플란트")
        
        Returns:
            [{rank, name, id, category, address, ...}, ...]
        """
        
        try:
            # 검색 페이지 접근
            url = self.BASE_URL.format(keyword)
            self.logger.info(f"[Scraping] Fetching {url}")
            
            # fetch_page_content: Playwright로 페이지 로드 + HTML wrapper 제거
            html_content = await self.fetch_page_content(url, scroll=False, is_mobile=False)
            
            if not html_content:
                self.logger.error(f"[HTML Scrape] Empty content for {keyword}")
                return []
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 검색 결과 추출
            results = self._extract_place_results(soup, keyword)
            
            self.logger.info(f"[HTML Scrape] Found {len(results)} places for '{keyword}'")
            return results
            
        except Exception as e:
            self.logger.error(f"[HTML Scrape Error] {type(e).__name__}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
    
    def _extract_place_results(self, soup: BeautifulSoup, keyword: str) -> List[Dict]:
        """
        BeautifulSoup 객체에서 장소 결과 추출
        
        Naver Maps HTML 구조 분석:
        - React로 렌더링되므로 구조가 복잡할 수 있음
        - 주요 정보가 data attributes나 aria-labels에 있을 수 있음
        """
        
        results = []
        
        # 전략 1: 표준 장소 아이템 찾기
        # Naver Maps에서 사용하는 다양한 class names
        place_selectors = [
            'div[class*="SearchResult"]',  # React component
            'li[class*="place"]',          # 리스트 아이템
            'div[class*="place_item"]',    # 개별 아이템
            '.place_name',                  # 이름
        ]
        
        self.logger.debug(f"[Scraping] Searching with {len(place_selectors)} selectors")
        
        # 방법 1: 최상위 컨테이너 찾기
        for selector in place_selectors:
            try:
                items = soup.select(selector)
                if items:
                    self.logger.debug(f"[Found] {len(items)} items with selector: {selector}")
                    
                    for rank, item in enumerate(items, 1):
                        result = self._parse_place_item(item, rank)
                        if result:
                            result['keyword'] = keyword
                            results.append(result)
                    
                    if results:
                        return results
            except Exception as e:
                self.logger.debug(f"[Selector Error] {selector}: {e}")
                continue
        
        # 방법 2: 텍스트 기반 검색
        # "검색 결과" 또는 "장소" 텍스트 포함 요소 찾기
        self.logger.debug("[Scraping] Trying text-based search...")
        
        divs = soup.find_all('div')
        for div in divs[:50]:  # 처음 50개만 검사
            text = div.get_text(strip=True)
            
            # 검색 결과처럼 보이는 텍스트
            if len(text) > 5 and len(text) < 100:
                # 주소 패턴: "서울시 중구..."
                if '시' in text and ('구' in text or '동' in text):
                    result = {
                        'rank': len(results) + 1,
                        'name': div.find_previous('div').get_text(strip=True) if div.find_previous('div') else 'Unknown',
                        'address': text,
                        'category': 'Unknown',
                        'id': '',
                        'road_address': text,
                        'lat': '',
                        'lng': '',
                        'keyword': keyword
                    }
                    results.append(result)
        
        self.logger.warning(f"[Scraping] Could not parse place items using standard selectors")
        self.logger.warning(f"[Scraping] HTML structure may have changed")
        
        # 방법 3: Script 태그에서 JSON 데이터 추출
        # Naver는 초기 데이터를 JavaScript로 인라인
        self.logger.debug("[Scraping] Trying script JSON extraction...")
        results = self._extract_from_script_data(soup, keyword)
        
        return results
    
    def _parse_place_item(self, item, rank: int) -> Optional[Dict]:
        """
        개별 장소 아이템 파싱
        
        추출 정보:
        - 이름 (name)
        - 카테고리 (category)
        - 주소 (road_address)
        - ID (Naver 내부 ID)
        """
        
        try:
            # 이름 추출
            name_elem = item.select_one('[class*="name"], .place_name, h3')
            name = name_elem.get_text(strip=True) if name_elem else ''
            
            # 카테고리 추출
            category_elem = item.select_one('[class*="category"], .category')
            category = category_elem.get_text(strip=True) if category_elem else ''
            
            # 주소 추출
            address_elem = item.select_one('[class*="address"], .address')
            address = address_elem.get_text(strip=True) if address_elem else ''
            
            # 링크/ID 추출
            link = item.select_one('a')
            place_id = link.get('href', '').split('/')[-1] if link else ''
            
            if not name:
                return None
            
            return {
                'rank': rank,
                'name': name,
                'id': place_id,
                'category': category,
                'road_address': address,
                'lat': '',  # HTML에서는 좌표를 얻기 어려움
                'lng': '',
            }
        
        except Exception as e:
            self.logger.debug(f"[Parse Error] {e}")
            return None
    
    def _extract_from_script_data(self, soup: BeautifulSoup, keyword: str) -> List[Dict]:
        """
        Script 태그의 JSON 데이터에서 추출
        React 앱이 window.__data = {...} 형식으로 저장할 수 있음
        """
        
        results = []
        
        try:
            scripts = soup.find_all('script')
            
            for script in scripts:
                content = script.string
                if not content:
                    continue
                
                # JSON 패턴 찾기
                if '__INITIAL_STATE__' in content or 'searchResult' in content:
                    self.logger.debug("[Script] Found potential data in script tag")
                    
                    # 간단한 파싱 (완전한 JSON 파싱은 복잡함)
                    # 실제 구현에서는 more sophisticated JSON 추출 필요
                    
                    import re
                    import json
                    
                    # JSON 객체 찾기
                    json_matches = re.findall(r'\{[^{}]*"(name|title)"[^{}]*\}', content)
                    
                    for match in json_matches:
                        self.logger.debug(f"[Script] Found potential result")
        
        except Exception as e:
            self.logger.debug(f"[Script Parse Error] {e}")
        
        return results
