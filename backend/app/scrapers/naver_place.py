import json
from app.scrapers.base import ScraperBase
import urllib.parse
from bs4 import BeautifulSoup
import re

class NaverPlaceScraper(ScraperBase):
    # This is the hidden GraphQL-like API used by Naver Map
    BASE_URL = "https://map.naver.com/p/api/search/allSearch?query={}&type=all&searchCoord=127.027610%3B37.498095" # Gangnam Coord as default

    async def get_rankings(self, keyword: str):
        encoded_keyword = urllib.parse.quote(keyword)
        url = self.BASE_URL.format(encoded_keyword)
        
        # This API requires a specific Referer and User-Agent to behave correctly
        # The base fetcher should handle UA, but we might need Referer if strict.
        
        response_text = await self.fetch_page_content(url, scroll=False)
        
        if not response_text:
            return []

        try:
            data = json.loads(response_text)

            # [DEBUG Issue #2] Log the API response structure for troubleshooting
            self.logger.debug(f"[Naver API] Response first 300 chars: {response_text[:300]}")
            self.logger.debug(f"[Naver API] Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'NOT_A_DICT'}")

            # Structure: result -> place -> list
            if 'result' not in data:
                self.logger.warning(f"[No Place Data] Missing 'result' key for keyword '{keyword}'. Available keys: {list(data.keys())}")
                self.logger.debug(f"[Full Response] {json.dumps(data, ensure_ascii=False)[:500]}")
                return []

            if not isinstance(data['result'], dict) or 'place' not in data['result']:
                # Sometimes it might be in 'address' or 'bus' if keyword is ambiguous,
                # but for dental keywords, it should be in 'place'.
                result_keys = list(data['result'].keys()) if isinstance(data['result'], dict) else 'NOT_A_DICT'
                self.logger.warning(f"[No Place Data] Missing 'place' key in result for keyword '{keyword}'. Result keys: {result_keys}")
                return []

            place_obj = data['result']['place']
            place_list = place_obj.get('list', []) if isinstance(place_obj, dict) else []

            if not place_list:
                self.logger.warning(f"[No Place Data] Empty place_list for keyword '{keyword}'")
                return []
                
            results = []
            for index, item in enumerate(place_list):
                results.append({
                    "rank": index + 1,
                    "name": item.get('name', ''),
                    "id": item.get('id', ''),
                    "category": item.get('category', ''),
                    "road_address": item.get('roadAddress', ''),
                    "keyword": keyword,
                    "lat": item.get('y', ''),
                    "lng": item.get('x', '')
                })
                
            return results

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse Naver Place JSON. Response len: {len(response_text)}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing Naver Place API: {e}")
            return []
