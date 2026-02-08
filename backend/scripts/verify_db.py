from app.core.database import SessionLocal
from app.models.models import Target
import uuid

def verify_db():
    db = SessionLocal()
    try:
        # Check if target already exists
        existing_target = db.query(Target).filter(Target.name == "Test Dental Clinic").first()
        if existing_target:
            print("Target already exists.")
            return

        new_target = Target(
            name="Test Dental Clinic",
            type="OWNER",
            urls={"blog": "http://blog.naver.com/test", "place": "http://place.naver.com/test"}
        )
        db.add(new_target)
        db.commit()
        print("Successfully inserted dummy target.")
        
        target = db.query(Target).filter(Target.name == "Test Dental Clinic").first()
        print(f"Retrieved target: {target.name}, ID: {target.id}")
        
    except Exception as e:
        print(f"Error verification DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_db()
