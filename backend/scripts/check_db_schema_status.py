
import sys
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from app.core.config import settings

def check_schema():
    print(f"Checking database schema at: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'LOCAL'}")
    
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"Found tables: {tables}")
    
    required_checks = {
        "daily_ranks": "client_id",
        "keywords": "client_id"
    }
    
    all_good = True
    
    for table, column in required_checks.items():
        if table in tables:
            columns = [c['name'] for c in inspector.get_columns(table)]
            if column in columns:
                print(f"[OK] Table '{table}' has column '{column}'.")
            else:
                print(f"[MISSING] Table '{table}' is MISSING column '{column}'.")
                all_good = False
        else:
            print(f"[MISSING] Table '{table}' does not exist.")
            all_good = False
            
    if not all_good:
        print("\n[CRITICAL] Database schema is out of sync with the code.")
        print("You MUST run a migration to add the missing columns before the application will work correctly.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Database schema matches the code changes.")

if __name__ == "__main__":
    check_schema()
