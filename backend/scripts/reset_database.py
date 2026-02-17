
import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.core.config import settings
from app.models.models import Base
from app.core.database import engine

def reset_database():
    """
    Resets the database by dropping all tables and recreating them.
    WARNING: This will delete ALL data in the database.
    """
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'LOCAL'}")
    
    try:
        # Test connection first
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("[SUCCESS] Database connection established.")
        
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("[SUCCESS] All tables dropped.")
        
        print("Creating all tables from models...")
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] All tables recreated with latest schema.")
        
        print("\nDatabase reset complete. All data has been cleared and schema is up to date.")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to reset database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    choice = input("WARNING: This will delete ALL data. Type 'DELETE' to confirm: ")
    if choice == "DELETE":
        reset_database()
    else:
        print("Operation cancelled.")
