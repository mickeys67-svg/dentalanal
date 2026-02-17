import time
import hashlib
import hmac
import base64
import requests
import json

# Provided Credentials
ACCESS_LICENSE = "0100000000e09241258b8714d0315208fa41f0dfda7d7ad755e70f926b8b514c0d1cd4a14e"
SECRET_KEY = "AQAAAADgkkEli4cU0DFSCPpB8N/amKaVDODTmRaTQ77teSEyIw=="
CUSTOMER_ID = "4286603" # From .env file (Mismatch with Cloud Run 2446031)
BASE_URL = "https://api.searchad.naver.com"

def generate_signature(timestamp, method, path):
    message = f"{timestamp}.{method}.{path}"
    hash = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(hash).decode('utf-8')

def get_headers(method, path):
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature(timestamp, method, path)
    return {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": ACCESS_LICENSE,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": signature
    }

def test_connection():
    path = "/ncc/campaigns"
    print(f"Testing connection to {BASE_URL}{path}...")
    headers = get_headers("GET", path)
    
    try:
        response = requests.get(BASE_URL + path, headers=headers, params={"size": 1})
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS! API Key and Secret are valid.")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"FAILED. Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_connection()
