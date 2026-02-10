from bs4 import BeautifulSoup
from app.scrapers.base import ScraperBase
import urllib.parse

class NaverAdScraper(ScraperBase):
    # Naver Search (PC)
    BASE_URL = "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={}"

    async def get_ad_rankings(self, keyword: str):
        encoded_keyword = urllib.parse.quote(keyword)
        url = self.BASE_URL.format(encoded_keyword)
        
        # Power links are usually visible on PC version
        html = await self.fetch_page_content(url, is_mobile=False)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Initial strategy: Look for the Power Link section
        # Class names change often, but usually contains "power_link" "ad" or similar IDs
        # Common structure: <div class="power_link_body"> ... <li class="lst_type">
        
        # Strategy 1: Look for explicit ad containers
        ad_list = soup.select(".power_link_body .lst_type > li")
        
        # Strategy 2: Fallback if class names changed
        if not ad_list:
            ad_list = soup.select("li.lst_type") # Broader selector

        if not ad_list:
             # Strategy 3: Look for 'ad' related classes
             ad_list = soup.select(".ad_section .lst_type > li")

        for index, item in enumerate(ad_list):
            try:
                # Extract Title/Headline
                # Usually in <div class="inner"> <a class="lnk_tit">
                title_tag = item.select_one(".lnk_tit")
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                
                # Extract Display URL / Domain
                # Usually <div class="url_area"> <a class="url">
                url_tag = item.select_one(".url_area .url")
                display_url = url_tag.get_text(strip=True) if url_tag else ""
                
                # Extract Description
                # Usually <div class="ad_dsc"> <p class="dsc">
                desc_tag = item.select_one(".ad_dsc .dsc")
                description = desc_tag.get_text(strip=True) if desc_tag else ""
                
                # Extract Advertiser Name (often same as title or part of display url)
                # We use display_url as identifier if title is generic
                advertiser = title # For now use title as advertiser name/brand
                
                results.append({
                    "rank": len(results) + 1,
                    "advertiser": advertiser,
                    "title": title,
                    "description": description,
                    "display_url": display_url,
                    "keyword": keyword
                })
                
            except Exception as e:
                self.logger.error(f"Error parsing ad item: {e}")
                continue

        if not results:
             self.logger.warning("No ads found. Saving HTML to debug_ad.html")
             with open("debug_ad.html", "w", encoding="utf-8") as f:
                 f.write(html)

        return results
