
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, UserRole, Client, Target, Keyword, DailyRank, PlatformType, Settlement, SettlementStatus
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import uuid
import random

router = APIRouter()

@router.post("/seed", status_code=201)
def seed_demo_data(
    db: Session = Depends(get_db),
    admin_secret: str = "dental1234" # Simple protection for demo endpoint
):
    """
    Seeds the database with demo data:
    - Admin User (admin@test.com / admin123!)
    - Sample Client (샘플 치과)
    - Targets (Competitors)
    - Keywords & Ranks
    - Settlement Data
    """
    if admin_secret != "dental1234":
        raise HTTPException(status_code=403, detail="Invalid secret")
        
    try:
        # 1. Create Admin User
        admin_email = "admin@test.com"
        admin = db.query(User).filter(User.username == admin_email).first()
        if not admin:
            admin = User(
                id=uuid.uuid4(),
                username=admin_email,
                email=admin_email,
                hashed_password=get_password_hash("admin123!"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin)
            print("Created Admin User")
            
        # 2. Create Sample Client
        client_name = "샘플 치과"
        client = db.query(Client).filter(Client.name == client_name).first()
        if not client:
            client = Client(
                id=uuid.uuid4(),
                name=client_name,
                industry="치과의원",
                agency_id=uuid.UUID("00000000-0000-0000-0000-000000000000")
            )
            db.add(client)
            print("Created Sample Client")
        
        db.flush() # Get IDs
        
        # 3. Create Keywords
        keywords_data = ["강남역 치과", "임플란트", "치아교정", "사랑니 발치"]
        keywords = []
        for kw_str in keywords_data:
            kw = db.query(Keyword).filter(Keyword.text == kw_str, Keyword.client_id == client.id).first()
            if not kw:
                kw = Keyword(
                    id=uuid.uuid4(),
                    text=kw_str,
                    client_id=client.id
                )
                db.add(kw)
            keywords.append(kw)
            
        # 4. Create Targets (Competitors + Owner)
        targets_data = [
            {"name": "샘플 치과", "type": "OWNER"},
            {"name": "라이벌 치과 A", "type": "COMPETITOR"},
            {"name": "강남 베스트 치과", "type": "COMPETITOR"},
        ]
        target_objs = []
        for t_data in targets_data:
            # Check if target exists (by name, for simplicity in demo)
            # Ideally should check client_id link but Target model link might be complex?
            # Let's just create new ones linked to client if supported, or global
            # For this demo, let's just create new ones if not exist
            t = db.query(Target).filter(Target.name == t_data["name"]).first()
            if not t:
                t = Target(
                    id=uuid.uuid4(),
                    name=t_data["name"],
                    type=t_data["type"]
                    # client_id might be needed if Target has it? Verify model
                )
                db.add(t)
            target_objs.append(t)
            
        db.flush()
        
        # 5. Create Daily Ranks (Past 7 days)
        today = datetime.now()
        for i in range(7):
            date = today - timedelta(days=i)
            for kw in keywords:
                for t in target_objs:
                    # Random rank between 1 and 30
                    rank_val = random.randint(1, 30)
                    
                    # Owner usually ranks better ;)
                    if t.name == "샘플 치과":
                        rank_val = random.randint(1, 5)
                        
                    dr = DailyRank(
                        id=uuid.uuid4(),
                        client_id=client.id,
                        target_id=t.id,
                        keyword_id=kw.id,
                        platform=PlatformType.NAVER_PLACE,
                        rank=rank_val,
                        captured_at=date
                    )
                    db.add(dr)

        # 6. Create Settlement (Last Month)
        last_month = today.replace(day=1) - timedelta(days=1)
        year, month = last_month.year, last_month.month
        
        settlement = db.query(Settlement).filter(
            Settlement.client_id == client.id, 
            Settlement.period == f"{year}-{month:02d}"
        ).first()
        
        if not settlement:
            settlement = Settlement(
                id=uuid.uuid4(),
                client_id=client.id,
                period=f"{year}-{month:02d}",
                total_spend=5000000,
                fee_amount=750000,
                tax_amount=75000,
                total_amount=5825000,
                status=SettlementStatus.PENDING,
                due_date=datetime(year, month+1 if month<12 else 1, 10)
            )
            db.add(settlement)
            print("Created Settlement")

        db.commit()
        return {"message": "Demo data seeded successfully!", "admin_email": admin_email}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
