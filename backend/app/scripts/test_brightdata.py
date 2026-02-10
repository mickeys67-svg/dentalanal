import asyncio
import os
import sys
from pathlib import Path

# Force UTF-8 for stdout
sys.stdout.reconfigure(encoding='utf-8')

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from app.scrapers.base import ScraperBase
from dotenv import load_dotenv

# Load env vars
load_dotenv()

async def test_scraping():
    scraper = ScraperBase()
    
    cdp_url = os.getenv("BRIGHT_DATA_CDP_URL")
    if not cdp_url:
        print("[WARN] BRIGHT_DATA_CDP_URL environment variable is NOT set.")
        print("Running in LOCAL mode (Headless Chrome). Bot detection is likely.")
    else:
        print(f"[OK] BRIGHT_DATA_CDP_URL found. Connecting to Bright Data...")

    # Test URL: Naver Search for a competitive keyword
    url = "https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EC%B9%98%EA%B3%BC+%EB%A7%88%EC%BC%80%ED%8C%85" # Query: 치과 마케팅
    
    print(f"Fetching URL: {url}")
    content = await scraper.fetch_page_content(url, scroll=True)
    
    if content:
        print(f"[OK] Successfully fetched content! Length: {len(content)} characters.")
        if "치과" in content:
            print("[OK] Content validation passed: Key term '치과' found in response.")
        else:
            print("[WARN] Content validation failed: Key term NOT found. Possible captcha or blocking.")
            
        # Optional: Save to file for inspection
        with open("brightdata_test_result.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("[INFO] Saved response to 'brightdata_test_result.html'")
    else:
        print("[ERR] Failed to fetch content. Empty response.")

if __name__ == "__main__":
    asyncio.run(test_scraping())
