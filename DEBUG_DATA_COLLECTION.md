# 🔍 대규모 디버깅: 데이터 수집 파이프라인 분석

**분석 일시**: 2026-02-20
**목표**: 데이터가 수집되지 않는 근본 원인 파악

---

## 📊 데이터 수집 파이프라인 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (프론트엔드): SetupWizard.tsx                          │
│ → "조사 시작" 버튼 클릭                                        │
│ → POST /api/v1/scrape/place                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend Endpoint: scrape.py                                    │
│ @router.post("/place")                                         │
│ → trigger_place_scrape()                                       │
│ → Concurrent task check (_active_scraping_tasks)              │
│ → background_tasks.add_task(scrape_place_task)               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Background Task: tasks.py                                      │
│ execute_place_sync()                                           │
│ → asyncio.run(run_place_scraper(keyword))                     │
│ → NaverPlaceScraper.get_rankings(keyword)                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Scraper: base.py                                               │
│ fetch_page_content(url)                                        │
│ → Connect to Browser (Local or Bright Data)                   │
│ → Navigate to Naver Maps API                                  │
│ → Extract JSON from page                                      │
│ → Return raw HTML/JSON                                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Parser: naver_place.py                                         │
│ Extract rankings from JSON:                                   │
│ data['result']['place']['list']                               │
│ → Parse each item                                             │
│ → Return List[dict] with rank, name, id, etc.               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Database Service: analysis.py                                  │
│ save_place_results(keyword, results)                           │
│ → Create/find Keyword in DB                                   │
│ → For each result:                                            │
│   - Create Target if not exists                              │
│   - Create DailyRank record                                   │
│   - Link to Keyword                                           │
│ → Commit transaction                                          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Database: Supabase/PostgreSQL                                  │
│ Tables: keywords, targets, daily_ranks                         │
│ → Data persisted                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔴 데이터 미수집 원인 (가설 분석)

### **원인 1: Bright Data CDP URL 미설정 또는 잘못된 형식** 🔴 높음

**코드 위치**: `base.py` 라인 25-44

```python
cdp_url = os.getenv("BRIGHT_DATA_CDP_URL")

if cdp_url and cdp_url.startswith("wss://"):
    # Connect to Bright Data
    browser = await p.chromium.connect_over_cdp(cdp_url)
else:
    # Fallback to local browser
    browser = await p.chromium.launch(headless=True)
```

**문제점**:
- ❓ `BRIGHT_DATA_CDP_URL` 환경변수 설정되어 있는가?
- ❓ 형식이 `wss://` 로 시작하는가?
- ❌ 로컬 브라우저로 폴백 시 성공하는가?

**테스트**:
```bash
# 1. 환경변수 확인
echo $BRIGHT_DATA_CDP_URL

# 2. 형식 확인
echo "wss://" 로 시작하는가?

# 3. 로컬 브라우저 테스트
# → Playwright가 설치되어 있는가?
# → headless=True 상태에서 연결 가능한가?
```

---

### **원인 2: Naver Maps API 응답 구조 변경** 🔴 높음

**코드 위치**: `naver_place.py` 라인 23-34

```python
try:
    data = json.loads(response_text)

    # Structure: result -> place -> list
    if 'result' not in data or 'place' not in data['result']:
        self.logger.warning(f"No Place data found in API for {keyword}")
        return []

    place_list = data['result']['place']['list']
```

**문제점**:
- ❓ API 응답에 `result.place.list` 가 있는가?
- ❌ API 응답 구조가 변경되었을 수 있음
- ❌ 빈 배열 `[]` 반환하면 데이터 수집 안 됨

**테스트**:
```bash
# 실제 API 응답 확인
curl "https://map.naver.com/p/api/search/allSearch?query=임플란트&type=all&searchCoord=127.027610%3B37.498095"

# 또는 Python으로
import json
import urllib.parse
keyword = "임플란트"
url = f"https://map.naver.com/p/api/search/allSearch?query={urllib.parse.quote(keyword)}&type=all"
# 브라우저로 방문해서 응답 확인
```

---

### **원인 3: 스크래핑 에러 로깅 부재** 🟠 중간

**코드 위치**: `tasks.py` 라인 48-52

```python
try:
    results = asyncio.run(run_place_scraper(keyword))
except Exception as e:
    logger.error(f"Scraping failed for {keyword}: {e}")
    error_msg = str(e)
    results = []  # ← 에러 시 빈 배열 반환!
```

**문제점**:
- ❌ 에러가 발생하면 `results = []`
- ❌ 빈 배열이면 데이터베이스 저장 안 함
- ❌ 사용자는 "데이터 없음"만 보임 (원인 모름)

**결과**:
```python
if results:  # ← 빈 배열이면 False
    service.save_place_results(keyword, results, client_uuid)
```

---

### **원인 4: 데이터베이스 저장 실패 (조용한 실패)** 🟠 중간

**코드 위치**: `tasks.py` 라인 85-92

```python
try:
    service = AnalysisService(db)
    if results:
        service.save_place_results(keyword, results, client_uuid)
    # ... 알림 추가
except Exception as e:
    logger.error(f"Saving place results or notifying failed: {e}")
    db.rollback()  # ← 롤백되어 데이터 손실!
```

**문제점**:
- ❌ 저장 실패해도 사용자는 "성공"으로 봄
- ❌ 트랜잭션 롤백 → 데이터 없음
- ❌ 에러 메시지가 백엔드 로그에만 있음

---

### **원인 5: Naver Ads API 미구현** 🟠 중간

**코드 위치**: `/api/v1/naver/ads` (naver_ads.py)

```python
# API 엔드포인트만 있고
# 실제 데이터 수집은 어디서?
```

**문제점**:
- ❓ 광고 데이터는 어디서 수집하는가?
- ❌ `/scrape/ad` 엔드포인트가 있나?
- ❌ Naver Ads API 클라이언트가 연동되었나?

---

### **원인 6: Keyword와 Target 미생성** 🟡 낮음

**코드 위치**: `analysis.py` 라인 31-43

```python
def _get_or_create_keyword(self, term: str, client_id: Optional[UUID] = None) -> Keyword:
    query = self.db.query(Keyword).filter(Keyword.term == term)
    if client_id:
        query = query.filter(Keyword.client_id == client_id)

    keyword = query.first()

    if not keyword:
        keyword = Keyword(id=uuid4(), term=term, client_id=client_id)
        self.db.add(keyword)
        self.db.commit()
```

**문제점**:
- ❓ Keyword 생성 실패하면?
- ❌ DailyRank가 어디에 연결되나?
- ❌ Foreign key constraint 위반 가능

---

## 🧪 디버깅 체크리스트

### Level 1: 환경변수 확인

```bash
# 1️⃣ Bright Data 설정
echo "BRIGHT_DATA_CDP_URL: ${BRIGHT_DATA_CDP_URL:0:20}..."

# 2️⃣ Naver API 설정
echo "NAVER_CLIENT_ID: ${NAVER_CLIENT_ID:0:10}..."
echo "NAVER_CLIENT_SECRET: ${NAVER_CLIENT_SECRET:0:10}..."

# 3️⃣ Naver Ads API 설정
echo "NAVER_AD_CUSTOMER_ID: $NAVER_AD_CUSTOMER_ID"
echo "NAVER_AD_ACCESS_LICENSE: ${NAVER_AD_ACCESS_LICENSE:0:10}..."
```

### Level 2: 백엔드 로그 확인

```bash
# 백엔드 컨테이너 로그 (Cloud Run)
gcloud run logs read dentalanal-backend --limit 100

# 특정 에러 필터
gcloud run logs read dentalanal-backend --limit 100 | grep -i "error\|fail\|exception"
```

### Level 3: 데이터베이스 상태 확인

```sql
-- Supabase SQL Editor에서

-- 1️⃣ Keywords 테이블
SELECT COUNT(*) as keyword_count FROM keywords;
SELECT * FROM keywords ORDER BY created_at DESC LIMIT 10;

-- 2️⃣ DailyRank 테이블
SELECT COUNT(*) as rank_count FROM daily_ranks;
SELECT * FROM daily_ranks ORDER BY date DESC LIMIT 10;

-- 3️⃣ Targets 테이블
SELECT COUNT(*) as target_count FROM targets;
SELECT * FROM targets LIMIT 10;

-- 4️⃣ RawScrapingLog 테이블 (존재하는가?)
SELECT COUNT(*) FROM raw_scraping_logs;
```

### Level 4: API 응답 직접 테스트

```bash
# 1️⃣ Naver Maps API 테스트
curl -X GET "https://map.naver.com/p/api/search/allSearch?query=임플란트&type=all&searchCoord=127.027610%3B37.498095" \
  -H "User-Agent: Mozilla/5.0"

# 2️⃣ SetupWizard API 호출 흐름
# - POST /api/v1/scrape/place (keyword="임플란트", client_id="...")
# - 응답 확인

# 3️⃣ 결과 폴링
# - GET /api/v1/scrape/results (client_id, keyword, platform)
# - 데이터 있는가?
```

---

## 📋 실제 실행해볼 검사 명령어

### Backend Health Check
```bash
# 1. 백엔드 health 확인
curl https://dentalanal-backend-xxx.run.app/health
# Expected: {"status": "ok"}

# 2. Naver Ads 수집 데이터 확인
curl -H "Authorization: Bearer {token}" \
  https://dentalanal-backend-xxx.run.app/api/v1/naver/collected-data
# Expected: Naver 데이터 반환
```

### Database Inspection
```sql
-- Supabase Console → SQL Editor

-- 최근 수집 데이터 확인
SELECT
  k.term,
  COUNT(dr.id) as rank_count,
  MAX(dr.date) as latest_date
FROM keywords k
LEFT JOIN daily_ranks dr ON k.id = dr.keyword_id
GROUP BY k.id, k.term
ORDER BY MAX(dr.date) DESC
LIMIT 20;

-- 에러 로그 확인
SELECT * FROM raw_scraping_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### Log Analysis
```bash
# Cloud Run 로그에서 "scrape" 관련 로그
gcloud run logs read dentalanal-backend --limit 200 | grep -A5 "scrape\|place\|naver"

# 에러 스택 트레이스 찾기
gcloud run logs read dentalanal-backend --limit 200 | grep -A10 "Exception\|Error\|Traceback"
```

---

## 🔧 즉시 적용 가능한 개선 사항

### 1️⃣ 스크래핑 에러 로깅 강화

```python
# tasks.py 수정 전
try:
    results = asyncio.run(run_place_scraper(keyword))
except Exception as e:
    logger.error(f"Scraping failed for {keyword}: {e}")

# 수정 후
import traceback
try:
    results = asyncio.run(run_place_scraper(keyword))
except Exception as e:
    logger.error(f"Scraping failed for {keyword}: {e}")
    logger.error(traceback.format_exc())  # ← 상세 스택 트레이스
    # Sentry 전송
    if sentry_sdk:
        sentry_sdk.capture_exception(e)
```

### 2️⃣ 데이터베이스 저장 에러 처리

```python
# 현재: 조용한 실패
try:
    service.save_place_results(...)
except Exception as e:
    logger.error(f"Failed to save: {e}")

# 개선: 사용자에게 알림
try:
    service.save_place_results(...)
except Exception as e:
    logger.error(f"Failed to save: {e}")
    # 보상 조치: Sentry 알림, Admin 통보
    sentry_sdk.capture_exception(e)
    # DLQ에 저장: Dead Letter Queue로 나중에 재시도
```

### 3️⃣ API 응답 검증

```python
# naver_place.py에 상세 검증 추가
try:
    data = json.loads(response_text)
    logger.debug(f"API Response keys: {data.keys()}")

    # 응답 구조 검증
    if 'result' not in data:
        logger.error(f"No 'result' key. Response: {str(data)[:200]}")
        return []

    if 'place' not in data['result']:
        logger.error(f"No 'place' key in result. Keys: {data['result'].keys()}")
        return []
```

---

## 🎯 다음 단계

1. **Level 1 검사**: 환경변수 확인
2. **Level 2 검사**: 백엔드 로그 분석
3. **Level 3 검사**: 데이터베이스 상태 조회
4. **Level 4 검사**: API 직접 테스트

각 단계마다 발견사항을 기록하고 패턴 분석

---

**작성일**: 2026-02-20
**다음 검토**: 디버깅 결과 수집 후
