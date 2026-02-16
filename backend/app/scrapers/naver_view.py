import json
from app.scrapers.base import ScraperBase
import urllib.parse
from bs4 import BeautifulSoup

class NaverViewScraper(ScraperBase):
    # Hidden API endpoint used by Naver Search (Mobile)
    # Returns JSON data directly!
    BASE_URL = "https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1&query={}&nlu_query=%7B%22r_category%22%3A%2225%22%7D&mod=2"

    async def get_rankings(self, keyword: str):
        encoded_keyword = urllib.parse.quote(keyword)
        url = self.BASE_URL.format(encoded_keyword)
        
        # We need a mobile user agent for this API usually, 
        # but the base Fetcher handles rotation.
        # This API returns a JSON-like structure or JSON with padding (JSONP).
        
        # Note: The response is actually JSON, so we just text() it and parse.
        response_text = await self.fetch_page_content(url, scroll=False)
        
        if not response_text:
            return []

        try:
            # Naver sometimes wraps valid JSON in parentheses or callback if JSONP
            # But this specific endpoint usually returns pure JSON.
            # Let's try parsing directly first.
            data = json.loads(response_text)
            
            # The structure is usually:
            # { "n_total": 1234, "contents": [ ... ] }
            
            if 'contents' not in data:
                self.logger.warning(f"Naver View API returned unexpected JSON structure for {keyword}")
                return []
                
            items = data['contents']
            results = []
            
            for index, item in enumerate(items):
                # Extract fields safely
                title = item.get('title', '').replace('<b>', '').replace('</b>', '') # Remove bold tags
                link = item.get('title_link', '')
                blog_name = item.get('writer_name', '')
                date = item.get('date', '')
                
                # Check for Ad (sometimes included)
                is_ad = item.get('is_ad', False)
                
                results.append({
                    "rank": index + 1,
                    "title": title,
                    "blog_name": blog_name,
                    "link": link,
                    "keyword": keyword,
                    "created_at": date,
                    "is_ad": is_ad
                })
                
            return results

        except json.JSONDecodeError:
            # Fallback (Just in case it returns HTML for some reason or IP block page)
            self.logger.error(f"Failed to parse Naver View JSON. Response might be HTML (Blocked?). Len: {len(response_text)}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing Naver View API: {e}")
            return []
