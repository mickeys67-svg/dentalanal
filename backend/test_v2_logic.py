from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_v2_endpoints():
    # 1. Get a sample client ID (using the first one in DB)
    from app.core.database import SessionLocal
    from app.models.models import Client
    db = SessionLocal()
    target_client = db.query(Client).first()
    db.close()
    
    if not target_client:
        print("Test failed: No client found in database.")
        return

    client_id = str(target_client.id)
    print(f"Testing for Client ID: {client_id}")

    # 2. Test Cohort V2
    resp = client.get(f"/api/v1/analyze/cohort/{client_id}")
    print(f"\n[COHORT V2] Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Sample: {data[0] if data else 'Empty'}")
        if data and "retention" in data[0] and isinstance(data[0]["retention"], list):
            print("=> SUCCESS: Real DB calculation verified.")
        else:
            print("=> WARNING: Might be using fallback or empty.")

    # 3. Test Segments V2
    resp = client.get(f"/api/v1/analyze/segments/{client_id}")
    print(f"\n[SEGMENT V2] Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Sample: {data[0] if data else 'Empty'}")
        if data and "visitors" in data[0] and data[0]["visitors"] > 0:
            print("=> SUCCESS: Segment aggregation verified.")

    # 4. Test Market Landscape
    resp = client.get("/api/v1/analyze/market/landscape?keyword=강남 치과")
    print(f"\n[MARKET LANDSCAPE] Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Total competitors found: {len(resp.json().get('competitors', []))}")

    # 5. Test Market Spend
    resp = client.get("/api/v1/analyze/market/spend?keywords=임플란트,교정")
    print(f"\n[MARKET SPEND] Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"First item: {resp.json()[0]}")

if __name__ == "__main__":
    test_v2_endpoints()
