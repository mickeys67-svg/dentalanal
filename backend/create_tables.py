from sqlalchemy import create_engine
from app.core.database import Base
from app.models.models import *
import os

# Directly using the URL to avoid env issues in this script
URL = "postgresql://postgres:miss418645!!~~@db.ugimcxylvgnmaiavylwf.supabase.co:5432/postgres"

def init_db():
    print(f"Connecting to {URL.split('@')[-1]}...")
    engine = create_engine(URL)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Tables created.")

if __name__ == "__main__":
    init_db()
