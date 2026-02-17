import sys
import os
import requests
import json
import time

# Configuration
BASE_URL = "https://dentalanal-backend-864421937037.us-west1.run.app"
TEST_EMAIL = "verifier_v2@example.com"
TEST_PASSWORD = "password123!"
TEST_CLIENT_NAME = "Verification Dental Clinic"

def log(msg, type="INFO"):
    print(f"[{type}] {msg}")

def run_verification():
    session = requests.Session()
    
    # 1. Signup (Create User)
    log("Step 1: Signup")
    signup_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "name": "Verifier",
        "role": "ADMIN"
    }
    resp = session.post(f"{BASE_URL}/api/v1/users/", json=signup_payload)
    if resp.status_code == 201:
        log("Signup Successful")
    elif resp.status_code == 400:
        log("User already exists, proceeding to login")
    else:
        log(f"Signup Failed: {resp.text}", "ERROR")
        return

    # 2. Login
    log("Step 2: Login")
    login_payload = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    resp = session.post(f"{BASE_URL}/api/v1/auth/login", data=login_payload)
    if resp.status_code != 200:
        log(f"Login Failed: {resp.text}", "ERROR")
        return
    
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    log("Login Successful, Token received")

    # 3. Create Client
    log("Step 3: Create Client")
    client_payload = {
        "name": TEST_CLIENT_NAME,
        "industry": "치과의원",
        "region": "Seoul"
    }
    resp = session.post(f"{BASE_URL}/api/v1/clients/", json=client_payload, headers=headers)
    if resp.status_code not in [200, 201]:
        log(f"Create Client Failed: {resp.text}", "ERROR")
        return
    
    client_data = resp.json()
    client_id = client_data['id']
    log(f"Client Created: {client_id}")

    # 4. Add Targets (Mock)
    log("Step 4: Add Targets")
    targets_payload = {
        "client_id": client_id,
        "targets": [
            {"name": TEST_CLIENT_NAME, "target_type": "OWNER", "url": "https://map.naver.com/v5/entry/place/12345"},
            {"name": "Competitor A", "target_type": "COMPETITOR", "url": "https://map.naver.com/v5/entry/place/67890"}
        ]
    }
    resp = session.put(f"{BASE_URL}/api/v1/targets/bulk", json=targets_payload, headers=headers)
    if resp.status_code != 200:
        log(f"Add Targets Failed: {resp.text}", "ERROR")
    else:
        log("Targets Added Successfully")

    # 5. Trigger Scrape (Place) - Async
    log("Step 5: Trigger Scrape")
    scrape_payload = {
        "keyword": "강남 치과",
        "client_id": client_id,
        "platform": "NAVER_PLACE"
    }
    # Note: Scrape endpoints might be different based on implementation
    # Assuming /api/v1/scrape/place or similar based on SetupWizard logic
    # SetupWizard calls: scrapePlace(keyword, newClientId!) -> likely /api/v1/scrape/place
    
    # Check endpoints first? Let's try the common path
    try:
        resp = session.post(f"{BASE_URL}/api/v1/scrape/place", json=scrape_payload, headers=headers)
        if resp.status_code == 202:
            log("Scrape Triggered Successfully (Async)")
        else:
            log(f"Scrape Trigger Warnings: {resp.status_code} {resp.text}", "WARN")
    except Exception as e:
        log(f"Scrape Trigger Failed: {e}", "WARN")

    # 6. Fetch Dashboard Data
    log("Step 6: Fetch Dashboard Data")
    # /api/v1/dashboard/stats/{client_id}
    resp = session.get(f"{BASE_URL}/api/v1/dashboard/stats/{client_id}", headers=headers)
    if resp.status_code == 200:
        log("Dashboard Stats Fetch Successful")
    else:
        log(f"Dashboard Stats Fetch Failed: {resp.status_code}", "ERROR")

    # 7. Cleanup
    log("Step 7: Cleanup (Delete Client)")
    resp = session.delete(f"{BASE_URL}/api/v1/clients/{client_id}", headers=headers)
    if resp.status_code == 200:
        log("Client Deleted Successfully")
    else:
        log(f"Client Delete Failed: {resp.text}", "ERROR")

    log("Verification Complete")

if __name__ == "__main__":
    try:
        run_verification()
    except requests.exceptions.ConnectionError:
        log("Could not connect to localhost:8000. Is the backend running?", "ERROR")
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
