import uuid
import datetime
import random
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Client, Lead, LeadActivity, LeadProfile, LeadEvent, PlatformType

def seed_analytics_v2():
    db = SessionLocal()
    try:
        # 1. Get a client to attach data to
        client = db.query(Client).first()
        if not client:
            print("No client found. Please create a client first.")
            return

        client_id = client.id
        print(f"Seeding data for client: {client.name} ({client_id})")

        # 2. Clear existing v2 data for this client (Optional - for clean seed)
        # db.query(Lead).filter(Lead.client_id == client_id).delete()
        # db.commit()

        # 3. Create leads for the last 5 months
        months = ["2023-10", "2023-11", "2023-12", "2024-01", "2024-02"]
        regions = ["강남구", "서초구", "송파구", "강동구", "기타"]
        channels = ["naver_ads", "google_search", "instagram", "organic"]
        
        for m_str in months:
            y, m = map(int, m_str.split("-"))
            num_leads = random.randint(50, 150)
            print(f"Creating {num_leads} leads for {m_str}...")
            
            for _ in range(num_leads):
                lead_id = uuid.uuid4()
                # Create Lead
                new_lead = Lead(
                    id=lead_id,
                    client_id=client_id,
                    name=f"Patient_{str(lead_id)[:6]}",
                    cohort_month=m_str,
                    channel=random.choice(channels),
                    first_visit_date=datetime.datetime(y, m, random.randint(1, 28))
                )
                db.add(new_lead)
                
                # Create Profile
                profile = LeadProfile(
                    id=uuid.uuid4(),
                    lead_id=lead_id,
                    device_type=random.choice(["mobile", "desktop"]),
                    region=random.choice(regions),
                    user_type=random.choice(["new", "returning"]),
                    total_visits=random.randint(1, 10),
                    total_conversions=random.randint(0, 2),
                    total_revenue=random.choice([0, 50000, 150000, 1200000])
                )
                db.add(profile)
                
                # Create Monthly Activities (Retention)
                # For each month from cohort month to current
                start_idx = months.index(m_str)
                for i in range(start_idx, len(months)):
                    # Active with some probability (retention curve)
                    offset = i - start_idx
                    prob = 0.8 ** offset # 100%, 80%, 64%...
                    
                    if random.random() < prob:
                        activity = LeadActivity(
                            id=uuid.uuid4(),
                            lead_id=lead_id,
                            activity_month=months[i],
                            visits=random.randint(1, 3),
                            conversions=1 if random.random() < 0.1 else 0,
                            revenue=random.choice([0, 0, 0, 50000])
                        )
                        db.add(activity)

            db.commit()

        print("Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_analytics_v2()
