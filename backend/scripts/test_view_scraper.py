import asyncio
import sys
import os

# Add backend directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

from app.scrapers.naver_view import NaverViewScraper

# Load .env manually for local test
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    print(f"Loading .env from {env_path}")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("'").strip('"')

async def main():
    scraper = NaverViewScraper()
    keyword = "임플란트"
    print(f"Testing NaverViewScraper (API Mode) with keyword: {keyword}")
    
    try:
        results = await scraper.get_rankings(keyword)
        
        if not results:
            print("No results found. Check API Keys.")
            return

        print(f"Found {len(results)} items.")
        for item in results[:10]:
            print(f"[{item['source_type']}] Rank {item['rank']}: {item['title']} ({item['blog_name']}) - {item['created_at']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
