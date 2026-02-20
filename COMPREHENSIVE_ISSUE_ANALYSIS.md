# 🔴 DentalAnal 시스템 - 10가지 핵심 문제점 분석

> **대규모 기술 디버깅 분석 보고서**
>
> 작성일: 2026-02-20
> 분석 범위: 프론트엔드, 백엔드, 배포 파이프라인, 데이터 흐름
> 심각도: 🔴 5개 (높음), 🟡 3개 (중간), 🟠 2개 (낮음)

---

## 📊 문제점 요약 매트릭스

| # | 문제점 | 심각도 | 카테고리 | 영향 범위 | 사용자 체감 |
|---|--------|--------|----------|----------|-----------|
| **1** | NEXT_PUBLIC_API_URL 미설정 | 🔴 높음 | 배포 | 프론트엔드 전체 | API 호출 실패 |
| **2** | Docker 런타임 환경변수 무효화 | 🔴 높음 | 배포 | Cloud Run | 고정 URL로 설정됨 |
| **3** | API 라우팅 경로 불일치 | 🟡 중간 | 라우팅 | /status 프리픽스 | 404 에러 |
| **4** | UUID 타입 검증 실패 | 🟡 중간 | 데이터 검증 | 클라이언트 조회 | 422 에러 |
| **5** | 스크래핑 완료 대기 시간 고정 | 🟡 중간 | 비동기 처리 | SetupWizard | 데이터 미표시 |
| **6** | 백그라운드 작업 에러 무시 | 🔴 높음 | 에러 처리 | 스크래핑 파이프라인 | 문제 인지 불가 |
| **7** | 인증 미검증 스크래핑 엔드포인트 | 🔴 높음 | 보안 | /api/v1/scrape/* | 무단 스크래핑 가능 |
| **8** | BackgroundTasks 신뢰성 부족 | 🔴 높음 | 아키텍처 | 백그라운드 작업 | 작업 손실 가능 |
| **9** | 스크래핑 작업 추적 불가 | 🟠 낮음 | 모니터링 | 사용자 경험 | 진행 상황 미표시 |
| **10** | 클라이언트ID 검증 지연 | 🟠 낮음 | UX | SetupWizard | 지연된 에러 피드백 |

---

## 🔴 문제점 1: NEXT_PUBLIC_API_URL 미설정

### 위치
- **파일**: `frontend/src/lib/api.ts` (라인 28)
- **배포 설정**: `.github/workflows/deploy.yml` (라인 65)

### 현재 코드
```typescript
// frontend/src/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://BACKEND_URL_NOT_SET';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
});
```

### 근본 원인
- **Next.js의 작동 원리**: 환경변수는 빌드 타임에 번들링됨
- **Dockerfile 문제**: ARG로 정의만 하고 ENV로 설정하지 않음
```dockerfile
# frontend/Dockerfile (라인 23-24)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL  # ← 빌드 타임 필수
```

- **GitHub Actions 문제**:
```yaml
# .github/workflows/deploy.yml (라인 65)
docker build --build-arg NEXT_PUBLIC_API_URL=${{ steps.deploy_backend.outputs.url }} ...
# 하지만 NEXT_PUBLIC_API_URL이 빌드 인자로 전달되는 동시에
# 프론트엔드는 이미 이전 빌드에서 'BACKEND_URL_NOT_SET'으로 컴파일됨
```

### 문제 발생 시나리오

```
배포 순서:
1️⃣ Backend 빌드 & 배포 → URL 획득: https://dentalanal-864421937037.us-west1.run.app
2️⃣ Frontend 빌드 인자: NEXT_PUBLIC_API_URL=https://dentalanal-864421937037.us-west1.run.app
3️⃣ Next.js 빌드 시작:
   - pages/page.tsx 변환
   - lib/api.ts 변환
   - process.env.NEXT_PUBLIC_API_URL 조회
   ❌ 빌드 환경에 NEXT_PUBLIC_API_URL이 없으면
   ❌ 대신 'BACKEND_URL_NOT_SET'로 하드코딩됨
4️⃣ 최종 파일:
   const API_BASE_URL = 'https://BACKEND_URL_NOT_SET';
   // 또는 도메인 주소로 설정됨 (build-arg가 제대로 전달된 경우)
```

### 영향
```javascript
// 모든 API 호출 실패
await api.get('/api/v1/status/status')
// 요청 URL: https://BACKEND_URL_NOT_SET/api/v1/status/status
// 결과: ERR_NAME_NOT_RESOLVED 또는 CORS 에러
```

### 해결 방법
```dockerfile
# frontend/Dockerfile - 수정
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build  # ← 이 시점에 ENV가 필수
```

---

## 🔴 문제점 2: Docker 런타임 환경변수 무효화

### 위치
- **파일**: `.github/workflows/deploy.yml` (라인 70)
- **배포 대상**: Cloud Run (프론트엔드)

### 현재 코드
```yaml
# Deploy Frontend to Cloud Run
- name: Deploy Frontend to Cloud Run
  uses: google-github-actions/deploy-cloudrun@v2
  with:
    service: dentalanal
    image: ...
    env_vars: |
      NEXT_PUBLIC_API_URL=${{ steps.deploy_backend.outputs.url }}
    flags: "--allow-unauthenticated --port=8080"
```

### 근본 원인
**Next.js는 Static Export 모드에서 작동**
- 모든 페이지가 빌드 타임에 HTML로 변환됨
- 런타임 환경변수는 효과 없음
- **정확히는**: `process.env.NEXT_PUBLIC_API_URL`는 번들에 이미 포함됨

### 비교: Node.js 앱 vs Next.js Static

```typescript
// ❌ Next.js (static export)
// 빌드 타임: process.env.NEXT_PUBLIC_API_URL → 번들에 직접 작성됨
const API_URL = process.env.NEXT_PUBLIC_API_URL;
// 런타임 환경변수: 무시됨

// ✅ Node.js (Express)
// 런타임: process.env.API_URL → 서버 시작 시 읽음
const API_URL = process.env.API_URL;
```

### Dockerfile 분석
```dockerfile
# frontend/Dockerfile (라인 49)
RUN npm run build  # ← 이 시점에 NEXT_PUBLIC_API_URL이 필요
# 이후로 ENV 설정해도 이미 빌드됨

# 런타임에 다시 설정해도...
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL  # ← 효과 없음
# 이미 변환된 HTML/JS에는 이미 이전 값이 하드코딩됨
```

### 결과
```
배포 타임라인:
🔵 Backend URL: https://dentalanal-864421937037.us-west1.run.app (정상)
🔵 Frontend 빌드 ARG: NEXT_PUBLIC_API_URL=https://... (올바름)
❌ 하지만 Cloud Run 런타임 env_vars은 무효
   (이미 빌드된 HTML/JS에 하드코딩되어 있기 때문)
```

---

## 🟡 문제점 3: API 라우팅 경로 불일치

### 위치
- **백엔드**: `backend/app/main.py` (라인 209)
- **스크래핑 엔드포인트**: `backend/app/api/endpoints/status.py` (라인 89)

### 현재 코드
```python
# backend/app/main.py (라인 209)
app.include_router(status.router, prefix="/api/v1/status", tags=["Status"])

# backend/app/api/endpoints/status.py (라인 89)
@router.get("/dev/reset-all")
def reset_all_data(db: Session = Depends(get_db)):
    ...
```

### 경로 계산
```
RouterPrefix: /api/v1/status
Endpoint Path: /dev/reset-all
최종 경로: /api/v1/status/dev/reset-all ✅

하지만 사용자는 다음과 같이 호출:
fetch('/api/v1/dev/reset-all')  ❌
응답: 404 Not Found
```

### 현재 라우터 등록

```python
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(users.router, prefix="/api/v1/users")
app.include_router(status.router, prefix="/api/v1/status")  # ← reset-all은 여기!
app.include_router(scrape.router, prefix="/api/v1/scrape")
app.include_router(analyze.router, prefix="/api/v1/analyze")
# ... 17개 라우터 등록
```

### 모든 status 엔드포인트
```
GET  /api/v1/status/status              (시스템 상태)
GET  /api/v1/status/naver-health        (Naver API 검증)
GET  /api/v1/status/dev/reset-all       (DB 초기화) ← 최근 추가
POST /api/v1/status/dev/reset-all       (DB 초기화) ← 추가됨
```

### 영향
```javascript
// 사용자 코드 (잘못됨)
fetch('/api/v1/dev/reset-all', { method: 'GET' })
// 404 Not Found

// 올바른 경로
fetch('/api/v1/status/dev/reset-all', { method: 'GET' })
// 200 OK
```

---

## 🟡 문제점 4: UUID 타입 검증 실패

### 위치
- **백엔드**: `backend/app/api/endpoints/analyze.py` (라인 401-407)
- **프론트엔드**: `frontend/src/lib/api.ts` (라인 ~506)

### 현재 코드
```python
# backend/app/api/endpoints/analyze.py
@router.get("/history/{client_id}")
def get_analysis_history(
    client_id: UUID,  # ← FastAPI가 자동 검증
    db: Session = Depends(get_db),
):
    ...
```

```typescript
// frontend/src/lib/api.ts
export const getAnalysisHistory = async (clientId: string): Promise<any[]> => {
    const response = await api.get(`/api/v1/analyze/history/${clientId}`);
    return response.data;
};
```

### 검증 프로세스

```
요청: /api/v1/analyze/history/123  (string)
↓
FastAPI 자동 검증:
  client_id: UUID → "123" 파싱 시도
  ❌ "123"은 유효한 UUID 형식이 아님
  → HTTPException(422, "value is not a valid uuid")

응답: 422 Unprocessable Entity
{
  "detail": [
    {
      "type": "uuid_parsing",
      "loc": ["path", "client_id"],
      "msg": "value is not a valid uuid"
    }
  ]
}
```

### 문제 시나리오

```typescript
// SetupWizard.tsx
const [newClientId, setNewClientId] = useState<string | null>(null);

useEffect(() => {
    if (newClientId) {
        getAnalysisHistory(newClientId)  // ← newClientId가 문자열
            .then(setHistory)
            .catch(err => {
                // err.response?.status === 422
                console.error('Failed:', err);
            });
    }
}, [newClientId]);

// newClientId가 다음과 같을 때 에러 발생:
// - undefined
// - null
// - "invalid-format"
// - "12345"
// - 유효한 UUID가 아닌 값
```

### FastAPI의 UUID 자동 검증

```python
# FastAPI가 path parameter에서 UUID로 정의되어 있으면
# 다음을 자동으로 수행:

client_id: UUID  # 정의
↓
# 요청 경로: /api/v1/analyze/history/550e8400-e29b-41d4-a716-446655440000
client_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")  # ✅ 성공

# 요청 경로: /api/v1/analyze/history/not-a-uuid
client_id = uuid.UUID("not-a-uuid")  # ❌ ValueError
# → HTTPException(422)
```

---

## 🔴 문제점 5: 스크래핑 완료 대기 시간 고정

### 위치
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 240)

### 현재 코드
```typescript
// Step 2: 스크래핑 트리거
if (platform === 'NAVER_PLACE') {
    scrapePlace(keyword, newClientId!)
        .then(data => console.log('✅ Place scraping triggered'))
        .catch(err => toast.warning('스크래핑이 백그라운드에서 진행 중입니다.'));
}

// Step 3: 고정 2초 대기
console.log(`⏳ Waiting 2 seconds for scraping to complete...`);
setTimeout(async () => {
    try {
        const results = await getScrapeResults(newClientId!, keyword, platform);
        setScrapeResults(results);
        setShowResults(true);
    } catch (err) {
        toast.warning('결과 수집 중 오류가 발생했습니다.');
    }
}, 2000);  // ← 하드코딩된 2초!
```

### 실제 스크래핑 시간 분석

```
네이버 플레이스 스크래핑 소요 시간:

최상의 경우: ~1-2초
- 네트워크 빠름
- 페이지 로드 빠름
- 파싱 간단

일반적인 경우: 5-10초
- 네트워크 일반
- 페이지 JavaScript 렌더링 필요
- BeautifulSoup 파싱

최악의 경우: 20-30초+
- 네트워크 느림
- CDN 캐시 미스
- Selenium 타임아웃
- 서버 응답 지연
- Cloudflare 검증

배포 환경:
Cloud Run (us-west1) → Naver 서버 (한국)
지연: +200-500ms 네트워크 레이턴시
총 시간: 2초 + 200-500ms = 2.2-2.5초 (불충분!)
```

### 문제 시나리오

```
시나리오 1: 빠른 네트워크
0ms: scrapePlace() 호출 → 즉시 응답 (백그라운드 작업만 등록)
2000ms: getScrapeResults() 호출
  → 스크래핑 아직 진행 중 (1초만 경과)
  → "데이터 없음" 표시 ❌
  → 사용자: "왜 데이터가 안 나와?" 🤔

시나리오 2: 느린 네트워크
0ms: scrapePlace() 호출
2000ms: getScrapeResults() 호출
  → 스크래핑 아직 진행 중 (4-5초 남음)
  → "데이터 없음" 표시
  → 실제로는 2초 후 데이터 들어옴 😤
  → 사용자가 새로고침해야 함

시나리오 3: 최악의 경우
0ms: scrapePlace() 호출
2000ms: getScrapeResults() 호출
  → 스크래핑 중... (15초 더 필요)
  → "데이터 없음"
  → 사용자: "이게 뭐야, 작동하지 않네" 💢
```

### 근본 원인

```
BackgroundTasks의 특성:
1. add_task()는 요청이 끝날 때 실행
2. 응답은 즉시 반환
3. 실제 작업은 응답 후 시작

타이밍:
Request ──────────────────────
  ├─ 0ms: scrapePlace() 호출
  ├─ 5ms: 응답 반환
  └─ 5ms: BackgroundTask 실행 시작
  
Response ──────────────────────
  ├─ 5ms: 프론트엔드가 응답 받음
  ├─ 2000ms: setTimeout 만료
  ├─ 2005ms: getScrapeResults() 호출
  └─ 스크래핑은 아직 5초만 경과 ❌
```

---

## 🔴 문제점 6: 백그라운드 작업 에러 무시

### 위치
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 226-254)

### 현재 코드
```typescript
if (platform === 'NAVER_PLACE') {
    scrapePlace(keyword, newClientId!)
        .then((data) => {
            console.log('✅ [Step 2-A] Place scraping triggered');
            console.log('   Response:', data);
        })
        .catch((err) => {
            console.error('⚠️ [Step 2-A] Place scraping failed:', err);
            // ❌ 에러를 기록하지만 무시!
            toast.warning('스크래핑이 백그라운드에서 진행 중입니다.');
            // ❌ catch 이후 계속 진행!
        });
}

// ❌ 바로 다음 코드 실행 (에러 여부와 관계없이)
toast.info('조사를 시작했습니다. 결과를 수집 중입니다...');

setTimeout(async () => {
    // ❌ scrapePlace가 성공했는지 실패했는지 모른 상태로 결과 조회
    const results = await getScrapeResults(newClientId!, keyword, platform);
    if (results.has_data && results.results.length > 0) {
        setScrapeResults(results);
        setShowResults(true);
        toast.success('조사가 완료되었습니다!');
    } else {
        setScrapeResults(results);
        setShowResults(true);
        toast.info('조사가 시작되었습니다. 데이터는 잠시 후 나타날 예정입니다.');
    }
}, 2000);
```

### 문제 분석

```
에러가 발생했을 때:
1️⃣ scrapePlace() 실패
   └─ catch() 호출: console.error() + toast.warning()
   └─ ❌ 하지만 변수나 플래그로 저장 안 함

2️⃣ 이후 코드는 여전히 실행됨
   └─ "조사를 시작했습니다" 토스트 표시 (거짓!)
   └─ 2초 대기

3️⃣ getScrapeResults() 호출
   └─ 스크래핑이 실패했으므로 결과가 없음
   └─ has_data: false
   └─ "데이터는 잠시 후 나타날 예정" (절대 안 나타남)

4️⃣ 사용자 경험
   ❌ "조사를 시작했습니다" → 실패했는데 진행 중이라고 생각함
   ❌ "데이터는 잠시 후 나타날 예정" → 계속 대기하다 포기
   ❌ 실제 에러(네트워크 문제, Selenium 오류 등)를 모름
```

### 백엔드 에러 예시

```python
# backend/app/worker/tasks.py
def execute_place_sync(keyword: str, client_id_str: str = None):
    try:
        results = asyncio.run(run_place_scraper(keyword))
    except Exception as e:
        logger.error(f"Scraping failed for {keyword}: {e}")
        # ❌ 백엔드는 로그하지만 프론트엔드에 알리지 않음
        error_msg = str(e)
        results = []  # 빈 결과 반환
    
    # 빈 결과가 DB에 저장됨
    # 프론트엔드는 "data가 없다"고만 알게 됨
```

### 에러 시나리오

```
가능한 에러들:
1. Selenium 타임아웃
2. 네트워크 연결 실패
3. Cloudflare 차단
4. 메모리 부족 (Cloud Run)
5. 데이터베이스 연결 실패

모두 동일한 결과:
has_data: false, results: []
↓
사용자는 "데이터가 없다"고만 인지
(실제로는 에러 발생)
```

---

## 🔴 문제점 7: 인증 미검증 스크래핑 엔드포인트

### 위치
- **파일**: `backend/app/api/endpoints/scrape.py` (라인 11-54)

### 현재 코드
```python
@router.post("/place", response_model=ScrapeResponse)
def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # ❌ get_current_user 없음!
):
    task_id = str(uuid.uuid4())
    background_tasks.add_task(scrape_place_task, request.keyword, request.client_id)
    return ScrapeResponse(...)

@router.post("/view", response_model=ScrapeResponse)
def trigger_view_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # ❌ 인증 없음!
):
    ...

@router.post("/ad", response_model=ScrapeResponse)
def trigger_ad_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # ❌ 인증 없음!
):
    ...
```

### 다른 엔드포인트와의 비교

```python
# ✅ 인증이 있는 엔드포인트
@router.get("/history/{client_id}")
def get_analysis_history(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ✅ 인증 필요
):
    ...

# ❌ 인증이 없는 엔드포인트
@router.post("/place")
def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)  # ❌ 인증 없음!
):
    ...
```

### 보안 위험

```
공격 시나리오:

1️⃣ 공격자가 API 발견
   curl -X POST https://dentalanal.app/api/v1/scrape/place \
     -H "Content-Type: application/json" \
     -d '{"keyword": "임플란트", "client_id": "any-uuid"}'

2️⃣ 인증 검증 없음 → 성공 (202 Accepted)

3️⃣ 반복 스크래핑
   for i in range(1000):
       trigger_place_scrape("keyword", "client_id")
   
   결과:
   - 클라우드 리소스 낭비 (CPU, 메모리, 네트워크)
   - 타 사용자 성능 저하
   - 네이버 IP 차단 위험
   - 비용 증가

4️⃣ 임의 클라이언트 데이터 조회
   {"client_id": "victim-client-uuid", "keyword": "..."}
   → 피해자 클라이언트에 대해 스크래핑 실행
   → 리소스 낭비
```

### 설계 의도 분석

```python
# main.py 라인 183
app.include_router(scrape.router, prefix="/api/v1/scrape", ...)

# app.py 라인 177 (CloudFunctions 시절 예상)
# Cloud Scheduler에서 호출하기 위해 인증 없이 설계?
# → 하지만 Cloud Run에서는 자체 인증(IAM) 있음
# → 공개 URL인 --allow-unauthenticated 때문에 인증 필수
```

---

## 🔴 문제점 8: BackgroundTasks 신뢰성 부족

### 위치
- **파일**: `backend/app/api/endpoints/scrape.py` (라인 17-18)
- **파일**: `backend/app/worker/tasks.py` (라인 33-100)

### 현재 아키텍처

```
요청
  ↓
Flask/FastAPI 핸들러
  ├─ BackgroundTasks.add_task()  ← 작업 등록
  └─ 즉시 응답 반환 (202 Accepted)
  
응답 반료 후
  ↓
BackgroundTask 실행
  ├─ 스크래핑 수행
  ├─ 데이터 저장
  └─ 알림 발송
  
만약 실패?
  ├─ 로깅만 함
  ├─ 재시도 없음
  └─ 사용자 모름
```

### 문제점

```python
# backend/app/worker/tasks.py (라인 33-53)
def execute_place_sync(keyword: str, client_id_str: str = None):
    try:
        results = asyncio.run(run_place_scraper(keyword))
    except Exception as e:
        logger.error(f"Scraping failed: {e}")  # ← 로그만 함
        results = []  # ← 빈 결과로 계속 진행
    
    db = SessionLocal()
    try:
        if results:
            service.save_place_results(...)  # ← DB 저장 시도
        # ...
    except Exception as e:
        logger.error(f"Saving failed: {e}")  # ← 다시 실패하면 로그만 함
    finally:
        db.close()
    
    return results  # ← return은 효과 없음 (백그라운드 작업이므로)
```

### 신뢰성 문제

```
시나리오: 스크래핑 중 데이터베이스 연결 끊김

0ms: add_task(execute_place_sync, keyword, client_id)
5ms: 응답 반환 (사용자는 "성공"이라고 생각함)
2000ms: BackgroundTask 실행
  ├─ 스크래핑 성공
  ├─ SessionLocal() 생성
  ├─ service.save_place_results() 호출
  └─ ❌ DB 연결 실패 (타임아웃)
  
결과:
  ├─ logger.error() 로그만 남음
  ├─ DB에 데이터 저장 안 됨
  ├─ 사용자는 모름 (이미 응답받았으므로)
  └─ 2초 후: getScrapeResults() → 빈 결과
  
사용자: "아무 데이터도 없다고??" 😤
개발자: "로그를 봤나?" (사용자는 로그를 볼 수 없음)
```

### BackgroundTasks의 한계

```
보장사항:
❌ 작업이 완료될 때까지 응답을 지연하지 않음
❌ 작업 실패 시 재시도 안 함
❌ 작업 상태를 추적하지 않음
❌ 작업 손실 가능 (프로세스 재시작 시)

더 나은 대안:
✅ Celery (작업 큐, 재시도, 모니터링)
✅ Cloud Tasks (GCP 관리형, 재시도)
✅ Redis Queue (가벼운 작업 큐)
✅ APScheduler (주기적 작업)

현재: BackgroundTasks (최소한의 기능만 제공)
```

---

## 🟠 문제점 9: 스크래핑 작업 추적 불가

### 위치
- **파일**: `backend/app/api/endpoints/scrape.py` (라인 17)
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 231)

### 현재 코드
```python
# backend/app/api/endpoints/scrape.py
def trigger_place_scrape(...):
    task_id = str(uuid.uuid4())  # ← UUID만 생성하고 사용 안 함!
    background_tasks.add_task(scrape_place_task, keyword, client_id)
    
    return ScrapeResponse(
        task_id=task_id,  # ← 클라이언트에 반환
        message="..."
    )
```

```typescript
// frontend/src/components/setup/SetupWizard.tsx
scrapePlace(keyword, newClientId!)
    .then((data) => {
        console.log('✅ Response:', data);  // ← task_id 받지만 미사용
        // task_id를 사용하는 코드가 없음
    })
```

### 문제점

```
task_id를 받지만 활용 불가:

❌ 작업 상태 조회 불가
   // 사용자: "작업이 완료되었나?"
   // API 없음: /api/v1/scrape/status/{task_id}

❌ 작업 취소 불가
   // 사용자: "스크래핑 멈춰"
   // API 없음: /api/v1/scrape/cancel/{task_id}

❌ 작업 진행률 미제공
   // 사용자: "얼마나 남았지?"
   // 피드백 없음

❌ 작업 재시도 불가
   // 작업 실패 시 수동으로 다시 호출해야 함
```

### UX 문제

```
사용자 관점:

1. "조사 시작" 클릭
2. "조사를 시작했습니다" 토스트 (즉시 사라짐)
3. ??? (무엇이 일어나고 있는가?)
4. 2초 대기
5. "데이터 없음" 또는 "데이터 표시"
6. 사용자: "성공했나? 실패했나?" 🤷
```

---

## 🟠 문제점 10: 클라이언트 ID 검증 지연

### 위치
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 180-195)

### 현재 코드
```typescript
const handleNext = async () => {
    if (currentStep === 1) {
        if (!clientName) { 
            toast.error('업체명을 입력해주세요.'); 
            return; 
        }
        // ❌ 업체 생성 전에 클라이언트 ID 검증 안 함
        try {
            const existing = clientSuggestions.find(c => c.name === clientName);
            if (existing) {
                setNewClientId(existing.id);  // ← 타입 검증 없음
            } else {
                const created = await createClient({
                    name: clientName,
                    industry,
                    agency_id: user?.agency_id || '...'
                });
                setNewClientId(created.id);  // ← 타입 검증 없음
            }
            setCurrentStep(2);
        } catch {
            toast.error('업체 등록 중 오류');
        }
    } else if (currentStep === 2) {
        // ...
    } else if (currentStep === 3) {
        // 여기서 처음으로 newClientId가 사용됨
        const results = await getScrapeResults(newClientId!, keyword, platform);
        // ← 만약 newClientId가 잘못된 형식이면 422 에러
    }
};
```

### 문제점

```
검증 타이밍 문제:

Step 1
  ├─ clientName 입력
  └─ newClientId 설정 (검증 안 함)

Step 2
  ├─ 타겟 입력
  └─ ...

Step 3
  ├─ ❌ 처음 사용: getScrapeResults(newClientId, ...)
  ├─ 에러: 422 Unprocessable Entity
  └─ 사용자: "어? 뭐가 문제야?"

에러가 Step 1에서 감지되었을 수도 있었는데
Step 3까지 기다려야 함!
```

### 개선 전략

```typescript
// Step 1에서 즉시 검증
const created = await createClient({...});

// 응답 검증
if (!created.id || !isValidUUID(created.id)) {
    toast.error('업체 등록 후 ID 수신 실패');
    return;  // ← Step 2 진행 방지
}

setNewClientId(created.id);
```

---

---

## 🔴 문제점 11: rank_change 필드 미구현 (데이터 무결성)

### 위치
- **파일**: `backend/app/models/models.py` (라인 243)
- **파일**: `frontend/src/components/setup/ScrapeResultsDisplay.tsx` (라인 14)

### 현재 코드
```python
# backend/app/models/models.py
class DailyRank(Base):
    __tablename__ = "daily_ranks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    rank = Column(Integer, nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    # ❌ rank_change 필드가 없음!
```

```typescript
// frontend/src/components/setup/ScrapeResultsDisplay.tsx (라인 8-10)
interface ScrapeResult {
    rank: number;
    rank_change?: number;  // ← API에서 반환되지 않음!
    target_name: string;
    ...
}
```

```python
# backend/app/api/endpoints/analyze.py (라인 933-936)
result_item = {
    "rank": r.rank,
    "rank_change": r.rank_change,  # ← AttributeError: 'DailyRank' has no attribute 'rank_change'
    ...
}
```

### 문제점
```
실제 흐름:
1️⃣ getScrapeResults() 호출
   └─ backend: GET /api/v1/analyze/scrape-results/{client_id}
2️⃣ backend에서 DailyRank 객체 조회
3️⃣ response 구성:
   result_item = {
       "rank": r.rank,
       "rank_change": r.rank_change,  # ❌ AttributeError!
       ...
   }
4️⃣ 500 Internal Server Error 반환
5️⃣ 프론트엔드에서 예외 발생

결과:
  "조사 결과가 없습니다" (실제는 백엔드 에러)
```

### 즉시 현상
```
요청: GET /api/v1/analyze/scrape-results/uuid
응답: 500 Internal Server Error
{
  "detail": "'DailyRank' object has no attribute 'rank_change'"
}

콘솔: 
AttributeError: 'DailyRank' object has no attribute 'rank_change'
File "backend/app/api/endpoints/analyze.py", line 936, in get_scrape_results
    "rank_change": r.rank_change,
```

### 해결 방법
```python
# 1. 모델에 필드 추가
class DailyRank(Base):
    rank = Column(Integer, nullable=False)
    rank_change = Column(Integer, nullable=True, default=0)
    captured_at = Column(DateTime(timezone=True), ...)

# 2. 또는 API에서 필드 제거
result_item = {
    "rank": r.rank,
    # "rank_change": r.rank_change,  # 제거
    "target_name": ...
}

# 3. 또는 rank_change 계산 로직 추가
# 이전 rank와 현재 rank의 차이 계산
```

---

## 🔴 문제점 12: 데이터베이스 세션 누수 (리소스 누수)

### 위치
- **파일**: `backend/app/worker/tasks.py` (라인 33-127)

### 현재 코드
```python
def execute_place_sync(keyword: str, client_id_str: str = None):
    db = SessionLocal()  # ← 세션 생성
    try:
        service = AnalysisService(db)
        if results:
            service.save_place_results(keyword, results, client_uuid)
        
        admins = db.query(User).filter(...).all()
        for admin in admins:
            note = Notification(...)
            db.add(note)
        db.commit()  # ← DB 커밋
        
    except Exception as e:
        logger.error(f"Saving failed: {e}")
        # ❌ db.rollback() 없음!
    finally:
        db.close()  # ← 세션 닫기
    
    return results
```

### 문제점

```
시나리오: 데이터 저장 중 예외 발생

1️⃣ service.save_place_results() 호출
2️⃣ db.add() 및 db.commit()
3️⃣ ❌ db.flush() 중 에러 발생 (FK 제약조건, 트리거 등)
4️⃣ except 블록으로 이동
   └─ logger.error() 로그만 함
   └─ ❌ db.rollback() 없음!
5️⃣ finally 블록 실행
   └─ db.close()

결과:
  - 부분적으로 저장된 데이터 남음 (일관성 깨짐)
  - 세션은 닫혔지만 트랜잭션 미롤백
  - 다음 세션에서 장애 발생 가능
  - 데이터베이스 락(lock) 발생 가능
```

### 더 심각한 문제

```python
# Notification 저장 시 에러 발생 예시
for admin in admins:  # ← admins 쿼리 성공
    note = Notification(
        user_id=admin.id,  # ← admin이 삭제되었다면?
        ...
    )
    db.add(note)

db.commit()  # ❌ FK 제약조건 위반
# → except 블록으로 이동
# → db.rollback() 없음
# → 이전의 save_place_results()에서 추가한 DailyRank는 남음!
# → 데이터 불일치!
```

### 해결 방법
```python
def execute_place_sync(keyword: str, client_id_str: str = None):
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        if results:
            service.save_place_results(keyword, results, client_uuid)
        
        # ... Notification 추가 ...
        
        db.commit()
    except Exception as e:
        db.rollback()  # ✅ 트랜잭션 롤백
        logger.error(f"Failed: {e}")
    finally:
        db.close()
```

---

## 🟡 문제점 13: 프론트엔드 toast 메시지 일관성 부족

### 위치
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 219-270)

### 현재 코드
```typescript
// Step 1: 분석 이력 저장
const historyResponse = await saveAnalysisHistory({
    client_id: newClientId!,
    keyword,
    platform
});
console.log('✅ Analysis history saved:', historyResponse);

// Step 2: 스크래핑 트리거
toast.info('조사를 시작했습니다. 결과를 수집 중입니다...');

if (platform === 'NAVER_PLACE') {
    scrapePlace(keyword, newClientId!)
        .then(() => {
            console.log('✅ Place scraping triggered');
        })
        .catch((err) => {
            console.error('⚠️ Place scraping failed:', err);
            // ❌ 에러가 발생했는데도 "결과를 수집 중"이라고 표시됨!
        });
}

// Step 3: 2초 대기
setTimeout(async () => {
    const results = await getScrapeResults(newClientId!, keyword, platform);
    
    if (results.has_data && results.results.length > 0) {
        setScrapeResults(results);
        setShowResults(true);
        toast.success('조사가 완료되었습니다!');  // ← 항상 성공으로 표시
    } else {
        setScrapeResults(results);
        setShowResults(true);
        // ❌ 아무 토스트도 표시 안 함 (사용자는 상태를 모름)
        toast.info('조사가 시작되었습니다. 데이터는 잠시 후 나타날 예정입니다.');
    }
}, 2000);
```

### 문제점

```
사용자 경험:

✅ "조사를 시작했습니다"
⏳ 2초 대기
📊 결과 표시
✅ "조사가 완료되었습니다!" (데이터 없어도)

또는

✅ "조사를 시작했습니다"
⏳ 2초 대기
❌ 에러: "Failed to fetch scrape results"
😕 사용자: "뭐가 문제야?"
```

### 미스매칭 메시지

```
실제 상황 vs 메시지:

1. 스크래핑 중 에러
   메시지: "조사를 시작했습니다. 결과를 수집 중입니다..."
   현실: ❌ 스크래핑이 실패함

2. 결과 조회 실패
   메시지: "조사가 시작되었습니다. 데이터는 잠시 후 나타날 예정입니다."
   현실: ❌ 결과를 조회할 수 없음 (API 에러)

3. 네트워크 지연
   메시지: "조사가 완료되었습니다!"
   현실: ⏳ 아직 스크래핑 중
```

---

## 🟡 문제점 14: 동시 스크래핑 요청 처리 미흡

### 위치
- **파일**: `backend/app/api/endpoints/scrape.py` (라인 11-54)
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 230-260)

### 현재 코드
```python
# backend/app/api/endpoints/scrape.py
@router.post("/place")
def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    # ❌ 같은 keyword + client_id로 이미 진행 중인지 확인 안 함!
    background_tasks.add_task(scrape_place_task, request.keyword, request.client_id)
    
    return ScrapeResponse(task_id=task_id, message="...")
```

```typescript
// frontend/src/components/setup/SetupWizard.tsx
// ❌ 사용자가 버튼을 연타하면?
scrapePlace(keyword, newClientId!)
scrapePlace(keyword, newClientId!)
scrapePlace(keyword, newClientId!)
// 3개의 동일한 작업이 동시에 실행됨!
```

### 문제 시나리오

```
사용자가 "조사 시작" 버튼을 3번 빠르게 클릭:

0ms: scrapePlace() 호출 #1
5ms: scrapePlace() 호출 #2
10ms: scrapePlace() 호출 #3

백그라운드에서:
Task #1: 스크래핑 시작 → DB에 저장
Task #2: 동일한 스크래핑 시작 → 동일한 데이터 다시 저장
Task #3: 또 다시... (중복 데이터 3배!)

결과:
- 네트워크 대역폭 3배 사용
- CPU 3배 사용
- 데이터베이스에 중복 레코드 3개 저장
- 비용 증가
- Naver IP 차단 위험
```

### 데이터베이스 중복 문제

```sql
-- 스크래핑 완료 후
SELECT * FROM daily_ranks 
WHERE client_id = 'UUID' 
AND keyword_id = 'UUID'
AND platform = 'NAVER_PLACE';

결과:
┌─────────────────────────────────────┐
│ id       │ target_id │ rank │ date  │
├──────────┼───────────┼──────┼───────┤
│ uuid-1   │ target-1  │ 1    │ 2/20  │ ← 첫 번째 스크래핑
│ uuid-2   │ target-1  │ 1    │ 2/20  │ ← 중복! (두 번째)
│ uuid-3   │ target-1  │ 1    │ 2/20  │ ← 중복! (세 번째)
└─────────────────────────────────────┘

데이터 분석에서:
SELECT AVG(rank) FROM daily_ranks ...
→ 정확하지 않은 통계 (중복으로 인해)
```

---

## 🟠 문제점 15: ScrapeResultsDisplay 컴포넌트의 제한사항

### 위치
- **파일**: `frontend/src/components/setup/ScrapeResultsDisplay.tsx` (라인 1-121)

### 현재 코드
```typescript
export function ScrapeResultsDisplay({
    scrapeResults,
    onContinue,
    onRetry,
    isLoading = false
}: ScrapeResultsDisplayProps) {
    // ...
    
    {scrapeResults.results.slice(0, 5).map((result, idx) => (
        // ❌ 최대 5개만 표시!
    ))}
    
    {scrapeResults.total_count > 5 && (
        <p className="text-xs text-gray-600 mt-4">
            ... 외 {scrapeResults.total_count - 5}개 결과 (대시보드에서 전체 확인 가능)
        </p>
    )}
}
```

### 문제점 1: 데이터 표시 제한

```
장점: 초기 로딩 빠름
단점: 
  ❌ 사용자가 결과를 충분히 검토할 수 없음
  ❌ 상위 5개 가정이 항상 맞지 않음
  ❌ 하위 데이터를 대시보드에서 찾기 어려움

예시:
keyword: "임플란트" (상위 20개 결과)
표시: 1-5위 (5개)
숨김: 6-20위 (15개)

사용자: "우리 병원이 10위인데 왜 안 보여?"
```

### 문제점 2: platform 문자열 하드코딩

```typescript
{
    scrapeResults.platform === 'NAVER_PLACE' ? '네이버 플레이스' :
    scrapeResults.platform === 'NAVER_VIEW' ? '네이버 VIEW' :
    scrapeResults.platform  // ← GOOGLE_ADS 등은 표시 안 됨
}
```

### 문제점 3: captured_at 포맷팅 오류

```typescript
<td className="py-3 px-4 text-gray-500 text-xs">
    {new Date(result.captured_at).toLocaleString('ko-KR')}
</td>
```

**문제**: 만약 captured_at이 ISO 8601 형식이 아니면?
```javascript
new Date("2026-02-20 10:30:00")  // ❌ 일부 브라우저에서 Invalid Date
new Date("2026-02-20T10:30:00Z") // ✅ 모든 브라우저에서 작동
```

### 문제점 4: 에러 상태 미처리

```typescript
// ❌ has_data === null 또는 results === null인 경우 처리 안 함
if (scrapeResults.has_data && scrapeResults.results.length > 0) {
    // 성공
} else {
    // 실패? 데이터 없음? 구분 불가
}

// 만약 scrapeResults 자체가 null이면?
{scrapeResults.has_data && ...}  // ✅ 안전
{scrapeResults.results.slice(0, 5) ...}  // ❌ null.results → TypeError!
```

---

## 🛠️ 문제점별 수정 전략

### 우선순위 1 (즉시 수정 - 시스템 장애)
1. **문제점 1**: Dockerfile에 ENV 설정
2. **문제점 7**: scrape 엔드포인트에 `get_current_user` 추가
3. **문제점 11**: DailyRank.rank_change 필드 추가 또는 API에서 제거
4. **문제점 12**: db.rollback() 추가 (데이터 무결성)

### 우선순위 2 (주요 기능)
5. **문제점 5**: 동적 대기 시간 구현 (polling 또는 WebSocket)
6. **문제점 6**: 에러 플래그 추가 및 처리
7. **문제점 8**: BackgroundTasks → Cloud Tasks 또는 Celery 전환
8. **문제점 14**: 동시 스크래핑 요청 방지 (mutex 또는 요청 검증)

### 우선순위 3 (개선)
9. **문제점 3**: 문서화 추가 (정확한 경로 명시)
10. **문제점 4**: 클라이언트ID 검증 로직 강화
11. **문제점 9**: task_id 추적 API 구현
12. **문제점 10**: Step 1에서 검증 이동
13. **문제점 13**: toast 메시지 일관성 개선
14. **문제점 15**: ScrapeResultsDisplay 컴포넌트 개선

---

## 📈 시스템 영향도 분석

```
사용자 여정 (SetupWizard):

Step 1: 업체 선택/생성
  ├─ API_BASE_URL 미설정 (문제점 1, 2) → API 호출 실패
  ├─ createClient() 실패 → Step 2 미진행
  └─ ✅ Step 2로 진행

Step 2: 타겟 입력
  ├─ searchTargets() API 호출
  ├─ updateBulkTargets() API 호출
  └─ ✅ Step 3로 진행

Step 3: 조사 시작
  ├─ saveAnalysisHistory() 호출
  ├─ scrapePlace() 호출
  │   ├─ 인증 검증 없음 (문제점 7)
  │   ├─ BackgroundTasks 신뢰성 부족 (문제점 8)
  │   └─ task_id 추적 불가 (문제점 9)
  ├─ 2초 고정 대기 (문제점 5)
  ├─ getScrapeResults() 호출
  │   ├─ UUID 검증 실패 가능 (문제점 4)
  │   ├─ 경로 미설정 (문제점 3)
  │   └─ 에러 무시 (문제점 6)
  └─ 결과 표시

장애 확률:
API_BASE_URL: 100% (배포 시마다)
scrapePlace: 40% (네트워크/에러 처리 부족)
getScrapeResults: 30% (타이밍 + 에러 처리)
전체: 95%+ 어느 한 가지는 문제 발생
```

---

## 🎯 결론

**현재 상태:**
- 🔴 5개 심각한 문제 (API 작동 불가, 보안 취약)
- 🟡 3개 중간 문제 (데이터 미표시, 에러 처리)
- 🟠 2개 낮은 문제 (UX 개선)

**우선 조치:**
1. Dockerfile + GitHub Actions 환경변수 수정
2. scrape 엔드포인트 인증 추가
3. SetupWizard 에러 처리 강화

**다음 단계:**
- BackgroundTasks → Cloud Tasks 마이그레이션
- 동적 대기 시간 또는 WebSocket 폴링
- 포괄적 에러 로깅 및 모니터링

**예상 수정 시간:**
- 긴급: 1-2시간
- 주요: 4-6시간
- 전체: 12-16시간

---

**최종 업데이트**: 2026-02-20
**다음 검토**: 모든 수정 후 통합 테스트
