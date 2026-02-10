import uuid
import logging
from app.core.database import SessionLocal, engine, Base
from app.models.models import Agency, Client, PlatformConnection, PlatformType, Keyword, Target

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db = SessionLocal()
    try:
        # Create Tables
        Base.metadata.create_all(bind=engine)
        
        # 1. Create Agency
        agency_name = "D-MIND 대행사"
        agency = db.query(Agency).filter(Agency.name == agency_name).first()
        if not agency:
            agency = Agency(id=uuid.uuid4(), name=agency_name)
            db.add(agency)
            db.commit()
            agency = db.query(Agency).filter(Agency.name == agency_name).first()
        
        agency_id = agency.id
        
        # 2. Create Clients
        client_a = db.query(Client).filter(Client.name == "A 치과").first()
        if not client_a:
            client_a = Client(id=uuid.uuid4(), agency_id=agency_id, name="A 치과", industry="의료")
            db.add(client_a)
        
        client_b = db.query(Client).filter(Client.name == "B 의원").first()
        if not client_b:
            client_b = Client(id=uuid.uuid4(), agency_id=agency_id, name="B 의원", industry="의료")
            db.add(client_b)
            
        db.commit()
        client_a = db.query(Client).filter(Client.name == "A 치과").first()
        client_a_id = client_a.id
        
        # 3. Create active connections for Client A
        existing_conn = db.query(PlatformConnection).filter(PlatformConnection.client_id == client_a_id).first()
        if not existing_conn:
            db.add(PlatformConnection(
                id=uuid.uuid4(),
                client_id=client_a_id,
                platform=PlatformType.NAVER_AD,
                status="ACTIVE",
                credentials={"api_key": "demo_key"}
            ))
            db.add(PlatformConnection(
                id=uuid.uuid4(),
                client_id=client_a_id,
                platform=PlatformType.META_ADS,
                status="ACTIVE",
                credentials={"access_token": "demo_token"}
            ))
            
        # 4. Add keywords
        if not db.query(Keyword).first():
            db.add(Keyword(id=uuid.uuid4(), term="임플란트", category="메인"))
            db.add(Keyword(id=uuid.uuid4(), term="치아교정", category="메인"))
            db.add(Keyword(id=uuid.uuid4(), term="강남역치과", category="지역"))
            
        db.commit()
        print(f"Seed complete. Agency Name: {agency_name}, Client A ID: {client_a_id}")
        
    except Exception as e:
        print(f"Seed failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
