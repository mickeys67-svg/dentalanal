import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.scrapers.naver_place import NaverPlaceScraper
from app.scrapers.naver_view import NaverViewScraper

async def test_scrapers():
    print("--- Starting Scraper Test ---")
    print(f"BRIGHT_DATA_CDP_URL: {'Set' if os.getenv('BRIGHT_DATA_CDP_URL') else 'Not Set'}")

    keyword = "송도 치과"
    
    print(f"\n1. Testing NaverPlaceScraper with keyword: {keyword}")
    place_scraper = NaverPlaceScraper()
    place_results = await place_scraper.get_rankings(keyword)
    print(f"Found {len(place_results)} items in Place search.")
    for res in place_results[:3]:
        print(f"  - Rank {res['rank']}: {res['name']}")

    print(f"\n2. Testing NaverViewScraper with keyword: {keyword}")
    view_scraper = NaverViewScraper()
    view_results = await view_scraper.get_rankings(keyword)
    print(f"Found {len(view_results)} items in View search.")
    for res in view_results[:3]:
        print(f"  - Rank {res['rank']}: {res['title']} ({res['blog_name']})")

    print("\n--- Scraper Test Completed ---")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
