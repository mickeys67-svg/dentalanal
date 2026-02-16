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
            
            # Structure: result -> place -> list
            if 'result' not in data or 'place' not in data['result']:
                # Sometimes it might be in 'address' or 'bus' if keyword is ambiguous, 
                # but for dental keywords, it should be in 'place'.
                self.logger.warning(f"No Place data found in API for {keyword}")
                return []
                
            place_list = data['result']['place']['list']
            if not place_list:
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
