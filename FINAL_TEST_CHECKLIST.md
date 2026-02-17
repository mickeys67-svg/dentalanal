# 🧪 최종 테스트 체크리스트

**배포 완료 후 실행할 항목들**

## Phase 5 엔드포인트 검증

### 1. GET /api/v1/reports/all (새 엔드포인트)
```
Endpoint: GET https://dentalanal-backend-864421937037.us-west1.run.app/api/v1/reports/all
Auth: Bearer token 필요
Expected: 200 OK, [] (빈 배열 - 클라이언트 없음)
```

### 2. POST /api/v1/reports/pdf/{id} (예정)
```
Endpoint: GET https://dentalanal-backend-864421937037.us-west1.run.app/api/v1/reports/pdf/test
Expected: PDF 또는 404 (리포트 없음)
```

### 3. POST /api/v1/reports/send-email (예정)
```
Endpoint: POST /api/v1/reports/send-email
Expected: 이메일 발송 또는 method not allowed
```

## Phase 4 엔드포인트 검증

### 4. POST /api/v1/analyze/competitors ✅
```
Request:
  {
    "keyword": "implant",
    "platform": "NAVER_PLACE",
    "top_n": 5
  }
Expected: 200 OK with competitor data
```

### 5. GET /api/v1/roi/* (예정)
```
Endpoint: GET /api/v1/roi/summary
Expected: 배포 확인
```

### 6. GET /api/v1/trends/* (예정)
```
Endpoint: GET /api/v1/trends/analysis
Expected: 배포 확인
```

## 시스템 기능 검증

### 7. 한글 로그 인코딩 확인
```
Check: /api/v1/status/status 의 recent_logs
Expected: 한글 정상 표시 (예: "플레이스 조사 결과 없음")
Before: "플랫폼 조사 결과..." (깨짐)
After: 정상 표시
```

### 8. 데이터 가용성
```
Clients: GET /api/v1/clients → 0개 (정상)
Keywords: GET /api/v1/analyze/targets/search → 8개 (샘플)
Templates: GET /api/v1/reports/templates → 1개
Reports: GET /api/v1/reports/all → 0개 (정상)
```

## 성능 및 안정성

### 9. 응답 시간 측정
- Login: < 1초
- Dashboard: < 2초
- Competitors: < 3초

### 10. 에러 핸들링
- 404 에러: 정상 반환
- 401 에러: 인증 오류 시
- 500 에러: 없어야 함

---

## 테스트 명령어

```bash
# 배포 후 실행
python check_endpoints.py    # 엔드포인트 상태 확인
python test_full_features.py # 전체 기능 테스트
python test_backend_bugs.py  # 버그 분석
```

## 배포 확인 URL

- **Swagger Docs**: https://dentalanal-backend-864421937037.us-west1.run.app/docs
- **Health Check**: https://dentalanal-backend-864421937037.us-west1.run.app/api/v1/status/status
- **OpenAPI Spec**: https://dentalanal-backend-864421937037.us-west1.run.app/openapi.json

---

**배포 예상 완료**: 2026-02-17 16:50 KST
**테스트 시작**: 배포 완료 후 5분
