
import sys
import os
import time
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.core.config import settings

def test_connection():
    url = settings.DATABASE_URL
    masked_url = url
    if "@" in url:
        masked_url = f"{url.split('://')[0]}://****@{url.split('@')[-1]}"
    
    print(f"Testing connection to: {masked_url}")
    
    try:
        engine = create_engine(url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"[SUCCESS] Connection successful! Result: {result.scalar()}")
            return True
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

if __name__ == "__main__":
    for i in range(3):
        print(f"\nAttempt {i+1}/3...")
        if test_connection():
            sys.exit(0)
        time.sleep(2)
    sys.exit(1)
