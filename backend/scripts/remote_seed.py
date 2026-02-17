import requests
import time
import sys

BASE_URL = "https://dentalanal-backend-864421937037.us-west1.run.app" 
# Or whatever the user's backend URL is. I will try to get it from .github but user needs to confirm.
# The user's provided URL in previous context was https://dentalanal-backend-864421937037.us-west1.run.app

def trigger_remote_seed():
    print(f"Triggering remote seed at {BASE_URL}...")
    try:
        # 1. Health check to ensure deployment is ready
        health = requests.get(f"{BASE_URL}/health")
        if health.status_code != 200:
            print(f"[WAIT] Server not ready yet. Status: {health.status_code}")
            return False
            
        # 2. Trigger Seed
        resp = requests.post(f"{BASE_URL}/api/v1/dev/seed?admin_secret=dental1234")
        
        if resp.status_code == 201:
            print("\n[SUCCESS] Remote seeding complete!")
            print(resp.json())
            return True
        else:
            print(f"\n[ERROR] Seeding failed: {resp.status_code} - {resp.text}")
            return True # Stop retrying on explicit error
            
    except Exception as e:
        print(f"[WAIT] Connection failed: {e}")
        return False

if __name__ == "__main__":
    for i in range(20): # Try for 2 minutes
        if trigger_remote_seed():
            sys.exit(0)
        time.sleep(6)
    print("Timeout waiting for deployment.")
