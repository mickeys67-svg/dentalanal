# 🚀 DentalAnal 배포 후 데이터 수집 문제 해결 가이드

**문제**: "아직도 안들어와 데이터 어떻게 하면 들어오는거야"
- SetupWizard에서 "조사시작" 버튼 클릭 후 데이터가 나타나지 않음
- 대시보드에 "아직 분석된 데이터가 없습니다" 메시지만 표시

**상황 분석**: 
- 디버그 엔드포인트 미배포 (404 에러) → ✅ 수정 완료
- 데이터 파이프라인 어디선가 중단됨

---

## 📋 Step-by-Step 진단 절차

### Phase 1: 환경 확인 (5분)

#### 1.1 Cloud Run 배포 상태 확인
```bash
# 최신 배포가 정상인지 확인
gcloud run services describe dentalanal-service --region us-west1 --format='value(status.observedGeneration,status.latestReadyRevision)'

# 최근 로그 확인 (배포 후 에러 없는지)
gcloud run logs read --service dentalanal --region us-west1 --limit 50
```

**기대 결과**:
- `status.latestReadyRevision`이 1개 이상
- 로그에 `[OK] database schema verified/patched.` 메시지
- 에러 없이 정상 시작

#### 1.2 API 접근성 확인
```bash
# 헬스체크
curl https://dentalanal-864421937037.us-west1.run.app/health
# 응답: {"status":"ok"}

# 디버그 엔드포인트 접근 (인증 필요)
curl -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  https://dentalanal-864421937037.us-west1.run.app/api/v1/debug/stats
```

**기대 결과**:
- 헬스체크: 200 OK
- 디버그 엔드포인트: 401 또는 정상 응답 (토큰 필요)
- 404 에러 없음

---

### Phase 2: 브라우저에서 진단 (5분)

#### 2.1 애플리케이션 로그인
1. https://dentalanal-864421937037.us-west1.run.app 접속
2. 로그인 (test@example.com / password)
3. 대시보드 페이지 확인 → "아직 분석된 데이터가 없습니다" 메시지 확인

#### 2.2 DevTools 네트워크 탭 열기
- F12 → Network 탭
- XHR/Fetch 필터 활성화
- 모든 요청 기록 시작

#### 2.3 SetupWizard 테스트
1. 좌측 메뉴에서 "새 조사 시작" 또는 설정 페이지로 이동
2. 클라이언트 생성 (또는 기존 클라이언트 선택)
3. 키워드 입력: "임플란트"
4. 플랫폼 선택: "Naver Search"
5. "조사시작" 버튼 클릭
6. Network 탭에서 다음 요청 확인:

   ```
   POST /api/v1/scrape/start ← 이 요청이 성공해야 함
   GET /api/v1/scrape/results ← 폴링 요청들 (여러 번 반복)
   ```

---

### Phase 3: 디버그 API 호출 (3분)

> **주의**: 이 단계는 **관리자 계정**으로 로그인되어 있어야 함

#### 3.1 빠른 통계 확인
브라우저 DevTools Console에서:
```javascript
fetch('/api/v1/debug/stats')
  .then(r => r.json())
  .then(d => console.log(JSON.stringify(d, null, 2)))
```

**기대 결과**:
```json
{
  "status": "success",
  "data": {
    "clients": 1,           // 0이면 문제!
    "keywords": 1,          // 0이면 문제!
    "daily_ranks": 5,       // 0이면 스크래핑 안됨
    "analysis_history": 1   // 분석 이력
  }
}
```

**문제 진단**:
- `clients: 0` → 클라이언트 생성이 안됨
- `keywords: 0` → 키워드가 저장 안됨
- `daily_ranks: 0` → 스크래핑이 안됨 또는 저장 안됨

#### 3.2 전체 진단 실행
같은 콘솔에서:
```javascript
fetch('/api/v1/debug/diagnose')
  .then(r => r.json())
  .then(d => console.log(JSON.stringify(d, null, 2)))
```

**기대 결과**: 모든 섹션이 데이터를 가지고 있어야 함

---

## 🔴 문제별 해결 방법

### 문제 1: `clients: 0`

**증상**: 
- 디버그 stats에서 clients 수가 0

**원인**:
- 클라이언트 생성 API 실패
- 또는 데이터베이스 저장 실패

**해결 방법**:

1️⃣ **브라우저 에러 메시지 확인**
   - Network 탭에서 POST /api/v1/clients 응답 확인
   - 에러 메시지 기록

2️⃣ **백엔드 로그 확인**
   ```bash
   gcloud run logs read --service dentalanal --region us-west1 --limit 100 | grep -i "client\|error"
   ```

3️⃣ **데이터베이스 직접 확인**
   - Supabase 대시보드 접속
   - `clients` 테이블 조회
   - 레코드 0개 확인

**빠른 해결**:
```sql
-- Supabase SQL Editor에서 실행
SELECT COUNT(*) FROM clients;
SELECT * FROM clients LIMIT 5;
```

---

### 문제 2: `keywords: 0` (clients는 있음)

**증상**:
- clients: 1 이상
- keywords: 0

**원인**:
- SetupWizard에서 키워드 저장 API 실패
- 또는 키워드 입력이 안됨

**해결 방법**:

1️⃣ **SetupWizard 입력 확인**
   - 키워드 입력 필드가 활성화되어 있는지 확인
   - 입력 후 값이 저장되는지 확인 (DevTools → Elements)

2️⃣ **API 요청 확인**
   - Network 탭에서 `/api/v1/analyze/history` 또는 유사 엔드포인트 찾기
   - 요청 본문(Body) 확인 → keyword 필드가 있는지
   - 응답 상태 코드 확인 (200이어야 함)

3️⃣ **백엔드 로그 확인**
   ```bash
   gcloud run logs read --limit 200 | grep -i "keyword\|analysis_history\|error"
   ```

---

### 문제 3: `daily_ranks: 0` (clients, keywords 있음) ⚠️ 가장 심각

**증상**:
- clients: 1 이상
- keywords: 1 이상  
- daily_ranks: 0 ← **스크래핑이 작동하지 않음**

**원인**:
1. 스크래핑 작업 미시작
2. 스크래핑 작업 실패 (에러 로그 안 남김)
3. 스크래핑은 되었지만 저장 안됨
4. 스크래핑은 되었지만 조회 안됨

**해결 방법**:

1️⃣ **SetupWizard에서 "조사시작" 후 폴링 확인**
   - Network 탭에서 `GET /api/v1/scrape/results?...` 반복 요청 확인
   - 만약 요청이 없으면 → SetupWizard 버튼이 작동 안함
   
2️⃣ **Cloud Run 로그에서 스크래핑 에러 찾기**
   ```bash
   gcloud run logs read --limit 500 | grep -iE "scrape|rank|naver|error|exception" | tail -50
   ```

   **찾아야 할 내용**:
   ```
   [Scraper] Starting scrape: keyword=임플란트, platform=NAVER_SEARCH
   [Scraper] Scraped rank=5
   [Scraper] Saved DailyRank
   ```
   
   또는
   ```
   [ERROR] Scraping failed: timeout
   [ERROR] Scraping failed: HTML parsing error
   [ERROR] Scraping failed: Connection refused
   ```

3️⃣ **Playwright/Chromium 문제 확인**
   ```bash
   # Cloud Run 로그에서 Playwright 에러 찾기
   gcloud run logs read --limit 500 | grep -iE "playwright|chromium|headless|timeout"
   ```

   **가능한 에러**:
   - `No space left on device` → Cloud Run 메모리 부족
   - `Timeout waiting for launch` → Playwright 시작 실패
   - `404 or 403` → Naver 차단 또는 IP 제한

---

## ⚡ 빠른 응급 처방

### Emergency Fix 1: 테스트 데이터 생성

API를 통한 테스트 데이터 주입:

```javascript
// 브라우저 콘솔에서 실행
fetch('/api/v1/status/dev/seed-test-data', { method: 'POST' })
  .then(r => r.json())
  .then(d => console.log('Seeding result:', d))
```

**기대 결과**:
```json
{
  "status": "success",
  "client_id": "...",
  "keywords_created": ["임플란트", "치아교정"],
  "daily_ranks_created": 10
}
```

그 후 다시 `/api/v1/debug/stats` 호출하면:
```json
{
  "clients": 1,
  "keywords": 2,
  "daily_ranks": 10  ← 0에서 10으로 증가!
}
```

### Emergency Fix 2: 타임아웃 증가

스크래핑이 timeout으로 실패하는 경우:

**파일**: `backend/app/scrapers/base.py`
```python
# 변경 전
TIMEOUT = 60  # 60초

# 변경 후
TIMEOUT = 180  # 180초 (3분)
```

그 후 배포:
```bash
git add backend/app/scrapers/base.py
git commit -m "[Hotfix] 스크래핑 타임아웃 증가 (60s → 180s)"
git push origin main
```

### Emergency Fix 3: 메모리 증가

Cloud Run에서 메모리 부족 에러 (`No space left on device`):

```bash
# Cloud Run 메모리를 2GB로 증가
gcloud run deploy dentalanal-service \
  --memory 2Gi \
  --region us-west1 \
  --update-env-vars "PYTHONUNBUFFERED=1"
```

---

## 📊 정상 데이터 흐름 확인

데이터가 정상 흐르는 경우의 완전한 체크리스트:

```
✅ 1. 브라우저: 로그인 성공
   └─ 토큰 얻음

✅ 2. SetupWizard: 클라이언트 생성
   └─ POST /api/v1/clients → 201
   └─ response: { id: "...", name: "..." }

✅ 3. SetupWizard: 키워드 입력 + "조사시작"
   └─ POST /api/v1/analyze/history → 201
   └─ response: { analysis_id: "..." }

✅ 4. Backend: 스크래핑 작업 시작
   └─ Cloud Run 로그: "Starting scrape: keyword=..."
   └─ Task: execute_place_sync or similar 실행

✅ 5. Backend: Naver 스크래핑
   └─ Playwright 브라우저 열기
   └─ 검색 페이지 접속
   └─ 순위 추출
   └─ 로그: "Scraped rank=..."

✅ 6. Backend: 데이터 저장
   └─ CREATE Keyword (if not exists)
   └─ CREATE Target (competitors)
   └─ CREATE DailyRank
   └─ 로그: "Saved DailyRank"

✅ 7. Frontend: 폴링
   └─ GET /api/v1/scrape/results?client_id=...&keyword=...
   └─ response: { ranks: [...] }

✅ 8. Frontend: UI 업데이트
   └─ 테이블이나 차트에 순위 데이터 표시
```

각 단계에서 ❌이면:
- 위의 문제별 해결 방법 참고
- Cloud Run 로그 분석

---

## 🔗 유용한 링크 및 명령어

### Cloud Run 관련
```bash
# 실시간 로그 (스트리밍)
gcloud run logs read --service dentalanal --region us-west1 --limit 100 -f

# 특정 에러 검색
gcloud run logs read --limit 1000 | grep -i "error\|exception\|failed"

# 배포 상태
gcloud run services describe dentalanal-service --region us-west1

# 최근 배포 목록
gcloud run revisions list --service dentalanal-service --region us-west1
```

### Supabase 관련
```sql
-- 클라이언트 데이터
SELECT id, name, created_at FROM clients LIMIT 10;

-- 키워드 데이터
SELECT id, term, client_id FROM keywords LIMIT 10;

-- 일일 순위 (가장 최근)
SELECT id, keyword_id, rank, platform, captured_at 
FROM daily_ranks 
ORDER BY captured_at DESC 
LIMIT 10;

-- 분석 이력
SELECT id, client_id, keyword, platform, created_at, is_saved
FROM analysis_history
ORDER BY created_at DESC
LIMIT 10;
```

### 데이터베이스 초기화 (마지막 수단)
```sql
-- ⚠️ 주의: 모든 데이터 삭제됨
DELETE FROM daily_ranks;
DELETE FROM targets;
DELETE FROM keywords;
DELETE FROM platform_connections;
DELETE FROM clients;

-- 다시 테스트 데이터 생성
POST /api/v1/status/dev/seed-test-data
```

---

## 🎯 체크리스트: 배포 후 확인 사항

배포 후 다음을 반드시 확인하세요:

- [ ] Cloud Run 배포 성공 (상태: Ready)
- [ ] 헬스체크 200 OK (/health)
- [ ] 로그인 가능
- [ ] 디버그 API 접근 가능 (/api/v1/debug/stats)
- [ ] 클라이언트 생성 가능
- [ ] 키워드 입력 및 저장 가능
- [ ] "조사시작" 클릭 후 폴링 요청 발생
- [ ] 5-30초 후 데이터 나타남
- [ ] 데이터베이스에 daily_ranks 기록 존재
- [ ] 대시보드에 데이터 차트 표시됨

---

**최종 확인**: 모든 체크리스트 항목이 완료되면 ✅ **데이터 수집 정상 작동**

문제가 지속되면 이 가이드의 "문제별 해결 방법" 섹션 참고.

