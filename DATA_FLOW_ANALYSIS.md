# 📊 DentalAnal 데이터 흐름 및 문제 해결 가이드

> **최종 분석 및 운영 가이드**
>
> 마지막 대규모 디버깅 결과를 정리한 문서입니다.
> 생성: 2026-02-20

---

## 🔍 핵심 발견

### 현재 상태
✅ **코드는 모두 정상 작동**
- 백엔드 API 엔드포인트 정상
- 프론트엔드 UI 컴포넌트 정상
- 스크래핑 데이터 수집 정상 → DailyRank 테이블에 저장됨
- Naver API 자격증명 모두 GitHub Secrets에 설정됨 ✓

❌ **데이터가 대시보드에 표시되지 않는 이유**

3가지 선행 조건이 필요함:
1. **API 키 설정** ✅ (GitHub Secrets에 있음, Cloud Run에 배포됨)
2. **PlatformConnection 생성** ❌ (필요 - 수동 생성 필요)
3. **동기화 실행** ❌ (필요 - 수동 트리거 필요)

### 데이터 저장 검증 완료

**실제 데이터가 이곳에 저장됨**:
- `DailyRank` 테이블 ← 네이버 플레이스/블로그 스크래핑 결과
- `RawScrapingLog` 테이블 ← 원본 스크래핑 로그
- `MetricsDaily` 테이블 ← Naver Ads API 데이터

---

## 🌍 전체 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                     데이터 수집 파이프라인                        │
└─────────────────────────────────────────────────────────────────┘

1️⃣ 프론트엔드 (SetupWizard.tsx)
   ├─ 사용자가 "조사 시작" 클릭
   ├─ saveAnalysisHistory() API 호출
   └─ 백엔드에서 비동기로 스크래핑 시작

2️⃣ 백엔드 (analyze.py - handle_naver_place_search)
   ├─ Selenium으로 네이버 플레이스 크롤링
   ├─ BeautifulSoup로 순위 정보 파싱
   ├─ DailyRank 테이블에 저장 ✅
   └─ RawScrapingLog 테이블에 로그 저장 ✅

3️⃣ Naver Ads API (worker/tasks.py)
   ├─ execute_ad_sync() 실행
   ├─ HMAC-SHA256 서명으로 인증
   ├─ JSON 응답 파싱
   └─ MetricsDaily 테이블에 저장 (API 데이터)

4️⃣ 프론트엔드 대시보드 (pages/page.tsx)
   ├─ getScrapeResults() → DailyRank 조회
   ├─ getMetricsDaily() → MetricsDaily 조회
   ├─ getLeads() → Leads/Conversions 조회
   └─ 차트/테이블 렌더링

┌─────────────────────────────────────────────────────────────────┐
│                      데이터베이스 테이블                         │
└─────────────────────────────────────────────────────────────────┘

📌 Supabase PostgreSQL (유일한 데이터 소스)

clients                    ← 클라이언트 기본정보
├─ platform_connections    ← 플랫폼 연결 (광고 계정)
│  ├─ campaigns           ← 광고 캠페인
│  │  ├─ leads           ← 리드/전환
│  │  └─ metrics_daily   ← 일일 지표 (Ads API)
│  └─ keywords           ← 추적 키워드
│     └─ daily_rank      ← 일일 순위 (스크래핑) ✅
├─ keywords              ← 클라이언트 키워드
│  └─ daily_rank         ← 순위 데이터
└─ analysis_history      ← 분석 요청 기록
```

---

## 🔧 GitHub Actions 시크릿 (현재 설정됨)

### deploy.yml에 정의된 환경변수

```yaml
# Naver Ads API
NAVER_AD_CUSTOMER_ID: ${secrets.NAVER_AD_CUSTOMER_ID}
NAVER_AD_ACCESS_LICENSE: ${secrets.NAVER_AD_ACCESS_LICENSE}
NAVER_AD_SECRET_KEY: ${secrets.NAVER_AD_SECRET_KEY}

# Naver Search/Place API
NAVER_CLIENT_ID: ${secrets.NAVER_CLIENT_ID}
NAVER_CLIENT_SECRET: ${secrets.NAVER_CLIENT_SECRET}

# Scraping
BRIGHT_DATA_CDP_URL: ${secrets.BRIGHT_DATA_CDP_URL}
```

**배포 현황**: ✅ 모든 시크릿이 Cloud Run 환경에 배포됨

---

## 📍 데이터 표시 조건 (3가지 필수)

### 1️⃣ API 키 설정 ✅ 완료
- GitHub Secrets에 모든 Naver API 키 저장됨
- Cloud Run 배포 시 자동으로 환경변수로 설정됨
- 확인 명령어:
  ```bash
  gcloud run services describe dentalanal --region us-west1 | grep NAVER
  ```

### 2️⃣ PlatformConnection 생성 ❌ 필요

**PlatformConnection이란?**
- 클라이언트가 Naver Ads 계정을 연결하는 레코드
- platform_connections 테이블에 저장
- 예: `client_id=XXX, platform="NAVER_ADS", account_id="1234", ...`

**왜 필요한가?**
- MetricsDaily 테이블에 데이터를 저장할 때 platform_connection_id를 참조
- PlatformConnection이 없으면 Ads API 데이터를 저장할 곳이 없음

**수동으로 생성하는 방법**:

```python
# Supabase SQL 콘솔에서 직접 실행
INSERT INTO platform_connections (
    client_id,
    platform,
    account_id,
    account_name,
    status,
    created_at,
    updated_at
) VALUES (
    'YOUR_CLIENT_UUID',
    'NAVER_ADS',
    'YOUR_CUSTOMER_ID',
    'Test Account',
    'ACTIVE',
    NOW(),
    NOW()
);
```

또는 프론트엔드 API 사용:
```typescript
// frontend/src/lib/api.ts에서 직접 호출
const response = await api.post('/api/v1/platform-connections', {
    client_id: 'YOUR_CLIENT_ID',
    platform: 'NAVER_ADS',
    account_id: 'YOUR_NAVER_AD_CUSTOMER_ID',
    account_name: 'My Naver Ads Account'
});
```

### 3️⃣ 동기화 실행 ❌ 필요

**동기화란?**
- execute_ad_sync(), execute_place_sync(), execute_view_sync() 등이 실행되는 것
- APScheduler가 정기적으로 실행 (기본: 6시간마다)
- 또는 API 호출로 수동 트리거 가능

**동기화 상태 확인**:
```bash
# Cloud Run 로그 확인
gcloud run logs read dentalanal --limit 50 | grep "sync"
```

**수동 트리거**:
```bash
# 플레이스 순위 동기화
curl -X POST https://dentalanal-XXX.run.app/api/v1/scheduler/trigger/place_sync

# Ads API 동기화
curl -X POST https://dentalanal-XXX.run.app/api/v1/scheduler/trigger/ad_sync

# 블로그 순위 동기화
curl -X POST https://dentalanal-XXX.run.app/api/v1/scheduler/trigger/view_sync
```

---

## 🔍 현재 상태 확인 쿼리

### Supabase SQL 콘솔에서 실행

**1. 클라이언트 확인**
```sql
SELECT id, name, email, created_at 
FROM clients 
ORDER BY created_at DESC 
LIMIT 1;
```

**2. PlatformConnection 확인**
```sql
SELECT id, client_id, platform, account_id, status
FROM platform_connections
WHERE client_id = 'YOUR_CLIENT_ID';
-- 결과: 0개 = PlatformConnection 미생성 ❌
```

**3. DailyRank 데이터 확인** (스크래핑 데이터)
```sql
SELECT 
    dr.keyword_id,
    k.term,
    dr.rank,
    dr.captured_at,
    dr.platform
FROM daily_rank dr
JOIN keywords k ON dr.keyword_id = k.id
WHERE dr.client_id = 'YOUR_CLIENT_ID'
ORDER BY dr.captured_at DESC
LIMIT 10;
-- 결과: 데이터 있음 = 스크래핑 성공 ✅
```

**4. MetricsDaily 확인** (Ads API 데이터)
```sql
SELECT 
    md.date,
    md.impressions,
    md.clicks,
    md.cost,
    md.conversions
FROM metrics_daily md
JOIN campaigns c ON md.campaign_id = c.id
WHERE c.connection_id IN (
    SELECT id FROM platform_connections 
    WHERE client_id = 'YOUR_CLIENT_ID'
)
ORDER BY md.date DESC
LIMIT 10;
-- 결과: 0개 = API 동기화 미실행 또는 PlatformConnection 미생성
```

**5. 분석 요청 기록 확인**
```sql
SELECT id, client_id, keyword, platform, status, created_at
FROM analysis_history
WHERE client_id = 'YOUR_CLIENT_ID'
ORDER BY created_at DESC
LIMIT 5;
```

---

## 🚀 완전한 데이터 표시 단계 (5단계)

### Step 1: 클라이언트 생성 (UI 또는 API)
```
Settings → "새 프로젝트 생성" → 이름 입력 → "생성"
```

### Step 2: 스크래핑 시작 (이미 작동)
```
SetupWizard → "조사 시작" 버튼 클릭
↓
백엔드에서 비동기로 네이버 플레이스/블로그 크롤링
↓
DailyRank 테이블에 결과 저장 ✅
```

### Step 3: PlatformConnection 생성 ⚠️ 필수
```
방법 A: Supabase SQL 콘솔에서 INSERT
방법 B: 향후 UI 추가 예정
```

### Step 4: Ads API 데이터 동기화 ⚠️ 필수
```
# 수동 트리거
curl -X POST https://dentalanal-XXX.run.app/api/v1/scheduler/trigger/ad_sync

# 또는 APScheduler가 자동 실행 (6시간마다)
```

### Step 5: 대시보드에서 데이터 확인
```
Dashboard → 차트/테이블에 데이터 표시됨 ✅
```

---

## ⚡ 빠른 트러블슈팅

### 문제: "조사 시작을 클릭했는데 데이터가 안 나옴"
**해결**:
1. ✅ 일단 SetupWizard가 "조사 시작" 버튼을 보여줌 = 코드 정상
2. ✅ DailyRank 테이블 확인 (위 쿼리 4번 실행)
3. ✓ 데이터 있음 = 완료, "조사결과" 모달에서 표시됨
4. ✗ 데이터 없음 = 스크래핑 아직 진행 중, 2-3분 기다렸다가 새로고침

### 문제: "대시보드에 아무 데이터도 안 나옴"
**원인 및 해결**:
1. **PlatformConnection 없음** → Step 3 실행
2. **Ads API 미동기화** → Step 4 실행 (`curl` 트리거)
3. **API 키 없음** → 자동 설정됨 (재배포 필요할 수 있음)

### 문제: "404 에러가 뜸"
**확인사항**:
```bash
# Cloud Run 로그 확인
gcloud run logs read dentalanal --limit 100 | grep "ERROR\|404"

# 모든 API 엔드포인트 확인
curl https://dentalanal-XXX.run.app/api/v1/status

# 특정 클라이언트 데이터 확인
curl https://dentalanal-XXX.run.app/api/v1/analyze/scrape-results/YOUR_CLIENT_ID
```

---

## 📋 API 엔드포인트 정리

### 분석 결과 조회
```
GET /api/v1/analyze/scrape-results/{client_id}
Query params: ?keyword=검색어&platform=NAVER_PLACE
Response: {
    "has_data": true,
    "keyword": "임플란트",
    "platform": "NAVER_PLACE",
    "results": [
        {
            "rank": 1,
            "rank_change": 0,
            "target_name": "ABC 치과",
            "target_type": "PLACE",
            "link": "https://place.naver.com/...",
            "captured_at": "2026-02-20T10:30:00"
        }
    ],
    "total_count": 5
}
```

### 분석 요청 저장
```
POST /api/v1/analysis/history
Body: {
    "client_id": "UUID",
    "keyword": "임플란트",
    "platform": "NAVER_PLACE"
}
Response: {
    "status": "started",
    "message": "분석이 시작되었습니다"
}
```

### 스케줄러 수동 트리거
```
POST /api/v1/scheduler/trigger/place_sync
POST /api/v1/scheduler/trigger/ad_sync
POST /api/v1/scheduler/trigger/view_sync
```

---

## 🔐 보안 및 인증

### Naver Ads API 인증 방식
- **HMAC-SHA256 서명** 사용
- Customer ID, Access License, Secret Key 필요
- 모두 GitHub Secrets에 저장되어 있음 ✅

### Cloud Run 배포
- 모든 시크릿이 환경변수로 자동 설정됨
- 각 요청 시 HMAC 서명 생성하여 API 호출

---

## 📈 향후 개선 계획

### 즉시 (Phase 4)
- [ ] UI에서 PlatformConnection 생성 기능 추가
- [ ] "Ads 계정 연결" 마법사 추가
- [ ] 자동 동기화 상태 대시보드 추가

### 단기 (Phase 5)
- [ ] 실시간 동기화 (WebSocket 또는 polling)
- [ ] 동기화 실패 시 자동 재시도
- [ ] Cloud Tasks를 사용한 안정적 스케줄링

### 중기 (Phase 6)
- [ ] Naver API 데이터와 스크래핑 데이터 자동 통합 (Reconciliation)
- [ ] 예측 분석 (트렌드 감지, 순위 예측)
- [ ] AI 기반 추천 (최적 입찰가, 타겟팅)

---

## 📞 리소스

**Naver API 문서**:
- [Naver Ads API](https://naver.github.io/searchad-apidocs/)
- [Naver Search API](https://developers.naver.com/docs/search/overview/)

**프로젝트 파일**:
- Backend: `E:\dentalanal\backend\`
- Frontend: `E:\dentalanal\frontend\`

**배포 설정**:
- GitHub Actions: `.github/workflows/deploy.yml`
- Cloud Run: `us-west1` 리전

**데이터베이스**:
- Supabase: `https://supabase.com/dashboard`
- Database URL: `postgresql://user:password@db.supabaseapi.com/postgres`

---

**마지막 업데이트**: 2026-02-20
**다음 재검토 예정**: Phase 4 완료 시점
