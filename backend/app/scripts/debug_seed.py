import uuid
import logging
from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models.models import (
    Agency, Client, PlatformConnection, PlatformType, Keyword, Target,
    DailyRank, TargetType
)

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
                platform=PlatformType.NAVER_PLACE,
                status="ACTIVE",
                credentials={"account_id": "demo_place"}
            ))
            db.add(PlatformConnection(
                id=uuid.uuid4(),
                client_id=client_a_id,
                platform=PlatformType.NAVER_VIEW,
                status="ACTIVE",
                credentials={"account_id": "demo_view"}
            ))

        # 4. Add keywords linked to Client A
        existing_keywords = db.query(Keyword).filter(Keyword.client_id == client_a_id).first()
        if not existing_keywords:
            db.add(Keyword(id=uuid.uuid4(), client_id=client_a_id, term="임플란트", category="메인"))
            db.add(Keyword(id=uuid.uuid4(), client_id=client_a_id, term="치아교정", category="메인"))
            db.add(Keyword(id=uuid.uuid4(), client_id=client_a_id, term="강남역치과", category="지역"))

        db.commit()

        # 5. Create Target records for testing
        target_owner = db.query(Target).filter(Target.name == "A 치과").first()
        if not target_owner:
            target_owner = Target(
                id=uuid.uuid4(),
                name="A 치과",
                type=TargetType.OWNER
            )
            db.add(target_owner)

        target_competitor1 = db.query(Target).filter(Target.name == "B 의원").first()
        if not target_competitor1:
            target_competitor1 = Target(
                id=uuid.uuid4(),
                name="B 의원",
                type=TargetType.COMPETITOR
            )
            db.add(target_competitor1)

        db.commit()

        # 6. Fetch created objects for linking
        keyword_implant = db.query(Keyword).filter(
            Keyword.client_id == client_a_id,
            Keyword.term == "임플란트"
        ).first()
        target_owner = db.query(Target).filter(Target.name == "A 치과").first()
        target_competitor1 = db.query(Target).filter(Target.name == "B 의원").first()

        # 7. Create sample DailyRank data for testing
        existing_ranks = db.query(DailyRank).filter(
            DailyRank.keyword_id == keyword_implant.id if keyword_implant else None
        ).first() if keyword_implant else None

        if not existing_ranks and keyword_implant and target_owner and target_competitor1:
            now = datetime.utcnow()

            # Create rank data from last 3 days (so polling finds recent data)
            for days_ago in range(0, 3):
                captured_at = now - timedelta(days=days_ago)

                # Owner rank
                db.add(DailyRank(
                    id=uuid.uuid4(),
                    client_id=client_a_id,
                    target_id=target_owner.id,
                    keyword_id=keyword_implant.id,
                    platform=PlatformType.NAVER_PLACE,
                    rank=3 + days_ago,  # 3, 4, 5
                    rank_change=-1 if days_ago > 0 else 0,
                    captured_at=captured_at
                ))

                # Competitor rank
                db.add(DailyRank(
                    id=uuid.uuid4(),
                    client_id=client_a_id,
                    target_id=target_competitor1.id,
                    keyword_id=keyword_implant.id,
                    platform=PlatformType.NAVER_PLACE,
                    rank=1 + days_ago,  # 1, 2, 3
                    rank_change=1 if days_ago > 0 else 0,
                    captured_at=captured_at
                ))

            db.commit()
            logger.info("Sample DailyRank data created for testing")

        print(f"✅ Seed complete!")
        print(f"   Agency: {agency_name}")
        print(f"   Client A ID: {client_a_id}")
        print(f"   Keywords: 임플란트, 치아교정, 강남역치과")
        print(f"   Platforms: NAVER_AD, NAVER_PLACE, NAVER_VIEW")
        print(f"   Sample ranking data created for testing polling feature")

    except Exception as e:
        print(f"❌ Seed failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
