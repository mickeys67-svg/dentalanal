import time
import hashlib
import hmac
import base64
import requests
import json

# --- 사용자 제공 정보 ---
CUSTOMER_ID = "4286603"
ACCESS_LICENSE = "0100000000e09241258b8714d0315208fa41f0dfda7d7ad755e70f926b8b514c0d1cd4a14e"
SECRET_KEY = "AQAAAADgkkEli4cU0DFSCPpB8N/amKaVDODTmRaTQ77teSEyIw=="

def generate_signature(timestamp, method, path, secret_key):
    message = f"{timestamp}.{method}.{path}"
    hash = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(hash).decode('utf-8')

def test_naver_api(path):
    base_url = "https://api.searchad.naver.com"
    method = "GET"
    timestamp = str(int(time.time() * 1000))
    
    signature = generate_signature(timestamp, method, path, SECRET_KEY)
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "X-Timestamp": timestamp,
        "X-API-KEY": ACCESS_LICENSE,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": signature
    }
    
    print(f"--- 네이버 API 테스트 호출 ({path}) ---")
    response = requests.get(base_url + path, headers=headers)
    
    print(f"상태 코드: {response.status_code}")
    print(f"응답 헤더: {response.headers.get('Content-Type')}")
    try:
        data = response.json()
        print("응답 데이터:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print("응답 본문 (JSON 아님):")
        if response.text:
            print(response.text)
        else:
            print("(비어 있음)")

if __name__ == "__main__":
    # 공식 문서상 NCC 접두사가 붙는 경우가 많으므로 확인
    endpoints = [
        "/ncc/managed-customer",
        "/ncc/ad-accounts",
        "/ncc/campaigns"
    ]
    
    for ep in endpoints:
        test_naver_api(ep)
        print("\n" + "="*40 + "\n")
