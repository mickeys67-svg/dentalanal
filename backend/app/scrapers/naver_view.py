from bs4 import BeautifulSoup
from app.scrapers.base import ScraperBase
import urllib.parse

class NaverViewScraper(ScraperBase):
    BASE_URL = "https://search.naver.com/search.naver?ssc=tab.blog.all&query={}&sm=tab_jum"

    async def get_rankings(self, keyword: str):
        encoded_keyword = urllib.parse.quote(keyword)
        url = self.BASE_URL.format(encoded_keyword)
        
        # Force PC version
        html = await self.fetch_page_content(url, scroll=True, is_mobile=False)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Robust extraction based on URL patterns
        # Identify all links to blog posts
        all_links = soup.find_all('a', href=lambda h: h and 'blog.naver.com' in h)
        
        import re
        processed_links = set()

        for link in all_links:
            href = link['href']
            
            # Pattern: blog.naver.com/blogId/postId (Post)
            # Pattern: blog.naver.com/blogId (Profile)
            
            # Match Post URL
            match = re.search(r'blog\.naver\.com/([a-zA-Z0-9_\-]+)/([0-9]+)', href)
            if match:
                blog_id = match.group(1)
                post_id = match.group(2)
                
                if href in processed_links:
                    continue
                processed_links.add(href)
                
                title = link.get_text(strip=True)
                # If title is empty/short (e.g. image link), skip or look for nested text
                if len(title) < 2: 
                    continue

                # Find Blog Name by searching nearby profile link
                blog_name = "Unknown"
                container = link.parent
                found_profile = False
                
                # Traverse up to find a container that includes the profile link
                for _ in range(6): # Go up 6 levels max
                    if not container or container.name == 'body': break
                    
                    # Search for profile link (blog.naver.com/blogId without postId)
                    # We look for a link that has blog_id but NOT post_id
                    candidates = container.find_all('a', href=lambda h: h and blog_id in h)
                    
                    for cand in candidates:
                         cand_href = cand.get('href', '')
                         if post_id not in cand_href:
                             # This is likely the profile link
                             text = cand.get_text(strip=True)
                             if text:
                                 blog_name = text
                                 found_profile = True
                                 break
                    
                    if found_profile: break
                    container = container.parent
                
                results.append({
                    "rank": len(results) + 1,
                    "title": title,
                    "blog_name": blog_name,
                    "link": href,
                    "keyword": keyword
                })

        if not results:
             print("No results extracted. Saving HTML to debug_view.html")
             with open("debug_view.html", "w", encoding="utf-8") as f:
                 f.write(html)

        return results
