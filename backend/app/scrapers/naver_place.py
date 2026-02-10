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
        
        # Updated selectors based on debug_place.html analysis
        # _list_item_sis14_40 is current mobile Map list item class
        items = soup.select("li._list_item_sis14_40, li._item, li.rE4H3, li[data-id]") 

        if not items:
            self.logger.warning("No items found using selectors. Saving HTML to debug_place.html")
            with open("debug_place.html", "w", encoding="utf-8") as f:
                f.write(html)

        for index, item in enumerate(items):
            try:
                name_tag = item.select_one("strong._item_name_sis14_275, span.place_bluelink, span.YwYLL")
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
