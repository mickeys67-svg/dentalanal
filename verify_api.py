import requests
import json
import os

BASE_URL = "https://dentalanal-backend-864421937037.us-west1.run.app"
# BASE_URL = "http://localhost:8000"

def run_verification():
    print(f"Targeting: {BASE_URL}")
    
    # 1. Login
    login_url = f"{BASE_URL}/api/v1/auth/login"
    payload = {
        "username": "admin@dmind.com",
        "password": "admin123!"
    }
    print(f"Logging in as {payload['username']}...")
    try:
        resp = requests.post(login_url, data=payload)
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data['access_token']
        print(f"Login successful. Token acquired.")
        print(f"User in token response: {token_data.get('user', 'N/A')}")
    except Exception as e:
        print(f"Login failed: {e}")
        if 'resp' in locals():
            print(resp.text)
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 2. Get Me (to check agency_id)
    # Note: I need to verify if /users/me endpoint exists. 
    # Based on main.py imports, 'users' router is mounted at /api/v1/users.
    # Let's check users.py again or guess /api/v1/auth/me if strictly auth related.
    # Usually it's /api/v1/users/me or /api/v1/auth/me
    
    # Trying /api/v1/users/ (list) first to see if I am in there
    print("Fetching users list...")
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/users/", headers=headers)
        resp.raise_for_status()
        # users = resp.json()
        # print(f"All Users: {json.dumps(users, indent=2, ensure_ascii=False)}")
        users = resp.json()
        me = next((u for u in users if u['email'] == "admin@dmind.com"), None)
        print(f"My User Info from list: {me}")
    except Exception as e:
        print(f"Failed to fetch users: {e}")
        if 'resp' in locals():
            print(resp.text)

    # 3. Create Client
    client_url = f"{BASE_URL}/api/v1/clients/"
    client_data = {
        "name": "서울마스터치과의원",
        "industry": "치과의원",
        "agency_id": "00000000-0000-0000-0000-000000000000"
    }
    print(f"Creating Client with data: {client_data}...")
    try:
        resp = requests.post(client_url, json=client_data, headers=headers)
        resp.raise_for_status()
        print(f"Client created successfully: {resp.json()}")
    except Exception as e:
        print(f"Client creation failed: {e}")
        if 'resp' in locals():
            print(resp.text)

    # 4. Check Status
    status_url = f"{BASE_URL}/api/v1/status/"
    print(f"Checking Status...")
    try:
        resp = requests.get(status_url, headers=headers)
        resp.raise_for_status()
        print(f"Status OK: {resp.json()}")
    except Exception as e:
        print(f"Status check failed: {e}")
        if 'resp' in locals():
            print(resp.text)

    # 5. Get Clients
    clients_url = f"{BASE_URL}/api/v1/clients/"
    print(f"Fetching Clients...")
    try:
        resp = requests.get(clients_url, headers=headers)
        resp.raise_for_status()
        print(f"Clients fetched: {len(resp.json())} items")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Get Clients failed: {e}")
        if 'resp' in locals():
            print(resp.text)



if __name__ == "__main__":
    run_verification()
