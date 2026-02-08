import asyncio
from app.scrapers.naver_place import NaverPlaceScraper
from app.scrapers.naver_view import NaverViewScraper

async def test_scrapers():
    print("Testing Naver Place Scraper...")
    place_scraper = NaverPlaceScraper()
    # Using a general keyword "송도 치과" to see if we can get results
    place_results = await place_scraper.get_rankings("송도 치과")
    print(f"Place Results: {len(place_results)} items found")
    for item in place_results[:3]:
        print(item)

    print("\nTesting Naver View Scraper...")
    view_scraper = NaverViewScraper()
    view_results = await view_scraper.get_rankings("송도 치과")
    print(f"View Results: {len(view_results)} items found")
    for item in view_results[:3]:
        print(item)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_scrapers())
