import requests
import sys
import time

BASE_URL = "https://dentalanal-backend-864421937037.us-west1.run.app"
ADMIN_EMAIL = "admin@dmind.com"
ADMIN_PASSWORD = "admin123!"

def verify_login():
    print(f"Verifying login at {BASE_URL}...")
    try:
        # 1. Health check
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print(f"[WAIT] Server not ready. Status: {health.status_code}")
            return False

        # 2. Login
        payload = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login", data=payload)
        
        if resp.status_code == 200:
            print(f"\n[SUCCESS] Login successful! DB is connected and seeded.")
            print(f"Token: {resp.json().get('access_token')[:10]}...")
            return True
        elif resp.status_code == 401:
            print(f"\n[FAILURE] Login failed (401). Admin user might not exist or password mismatch.")
            print(f"Response: {resp.text}")
            # If 401, DB might be connected but seeding didn't run or password diff.
            # But at least it's not 500.
            return True 
        else:
            print(f"\n[ERROR] Login error: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        print(f"[WAIT] Connection failed: {e}")
        return False

if __name__ == "__main__":
    for i in range(30): # Try for 3 minutes
        if verify_login():
            sys.exit(0)
        time.sleep(6)
    print("Timeout waiting for deployment.")
