from pymongo import MongoClient
from app.core.config import settings
import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MongoService:
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGODB_URL)
            self.db = self.client.get_database() # Uses database name from URL or default
            self.raw_data = self.db.raw_scraping_data
            logger.info("MongoDB connection established.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None

    def save_raw_result(self, platform: str, keyword: str, data: Any, metadata: Dict[str, Any] = None):
        """Saves unstructured scraping results to MongoDB."""
        if not self.client:
            logger.warning("MongoDB client not initialized. Skipping save.")
            return None
        
        doc = {
            "platform": platform,
            "keyword": keyword,
            "data": data,
            "metadata": metadata or {},
            "captured_at": datetime.datetime.utcnow()
        }
        
        try:
            result = self.raw_data.insert_one(doc)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
            return None

    def get_latest_results(self, platform: str, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent raw data from MongoDB."""
        if not self.client: return []
        
        return list(self.raw_data.find(
            {"platform": platform, "keyword": keyword}
        ).sort("captured_at", -1).limit(limit))
