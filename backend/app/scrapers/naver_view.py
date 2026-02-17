from app.scrapers.base import ScraperBase
from app.external_apis.naver_search import NaverSearchClient
import logging

class NaverViewScraper(ScraperBase):
    """
    Refactored to use Official Naver Search API (Blog & Cafe).
    Replaces the previous scraping method which is blocked.
    """
    
    def __init__(self):
        super().__init__()
        self.api_client = NaverSearchClient()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_rankings(self, keyword: str):
        if not self.api_client.client_id:
             self.logger.error("Naver API Client ID not configured. Cannot fetch View data.")
             return []

        try:
            self.logger.info(f"Fetching Naver View (API) for: {keyword}")
            
            # Fetch Blog and Cafe results
            # Display: 50 Blogs, 20 Cafes
            blog_data = await self.api_client.search_blog(keyword, display=50, sort='sim')
            cafe_data = await self.api_client.search_cafe(keyword, display=20, sort='sim')
            
            items = []
            
            # Helper to process items
            def process_items(source_items, source_type):
                processed = []
                for item in source_items:
                    # Strip tags
                    title = item.get('title', '').replace('<b>', '').replace('</b>', '').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    desc = item.get('description', '').replace('<b>', '').replace('</b>', '').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    link = item.get('link', '')
                    date = item.get('postdate', '')
                    
                    # Formatting date YYYYMMDD -> YYYY-MM-DD
                    if len(date) == 8:
                        date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                    
                    blog_name = item.get('bloggername') or item.get('cafename') or source_type
                    
                    processed.append({
                        "title": title,
                        "blog_name": blog_name,
                        "link": link,
                        "keyword": keyword,
                        "created_at": date,
                        "is_ad": False, 
                        "snippet": desc,
                        "source_type": source_type
                    })
                return processed

            # Combine Blog and Cafe
            items.extend(process_items(blog_data.get('items', []), "Blog"))
            items.extend(process_items(cafe_data.get('items', []), "Cafe"))
            
            # Re-assign ranks based on list order
            results = []
            for index, item in enumerate(items):
                item['rank'] = index + 1
                results.append(item)
            
            self.logger.info(f"Fetched {len(results)} items via Naver API for {keyword}")
            return results

        except Exception as e:
            self.logger.error(f"Error using Naver API: {e}")
            return []
