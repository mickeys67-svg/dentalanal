from bs4 import BeautifulSoup
from app.scrapers.base import ScraperBase
import urllib.parse

class NaverPlaceScraper(ScraperBase):
    BASE_URL = "https://m.map.naver.com/search2/search.naver?query={}&sm=hty&style=v5"

    async def get_rankings(self, keyword: str):
        encoded_keyword = urllib.parse.quote(keyword)
        url = self.BASE_URL.format(encoded_keyword)
        
        html = await self.fetch_page_content(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # This selector needs to be adjusted based on actual Naver Map Mobile HTML structure
        # Assuming list items are in some list container. 
        # Note: Naver Map is dynamic, heavy JS. Playwright handles the rendering.
        # We look for the specific elements that represent the place list.
        
        # Updated selectors to be more robust against dynamic class suffixes
        items = soup.select("li[class*='_list_item'], li._item, li.rE4H3, li[data-id], .place_list li, .sc_list li")

        if not items:
            title = soup.title.string if soup.title else "No Title"
            body_text = soup.body.get_text(separator=' ', strip=True)[:1000] if soup.body else "No Body"
            self.logger.warning(f"No items found. Page Title: {title}, HTML Len: {len(html)}")
            self.logger.warning(f"Page Text Snippet: {body_text}")
            
            # Still save to local file for local debugging if possible
            with open("debug_place.html", "w", encoding="utf-8") as f:
                f.write(html)

        for index, item in enumerate(items):
            try:
                name_tag = item.select_one("strong[class*='_item_name'], strong._item_name_sis14_275, span.place_bluelink, span.YwYLL")
                if name_tag:
                    name = name_tag.text.strip()
                    results.append({
                        "rank": index + 1,
                        "name": name,
                        "keyword": keyword
                    })
            except Exception as e:
                self.logger.error(f"Error parsing item: {e}")
                continue
                
        return results
