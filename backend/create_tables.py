from app.core.database import engine, Base
from app.models.models import *

def create_tables():
    print("Creating all missing tables in the database...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
