import requests
import json

url = "http://localhost:8000/api/v1/analyze/ai-report"
payload = {
    "keyword": "송도 치과",
    "target_hospital": "송도퍼스트치과",
    "platform": "NAVER_PLACE",
    "top_n": 10
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("✅ AI 리포트 생성 성공!")
        data = response.json()
        print("-" * 50)
        print(data["report"][:500] + "...") # 앞부분만 출력
        print("-" * 50)
    else:
        print(f"❌ 요청 실패: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ 에러 발생: {str(e)}")
