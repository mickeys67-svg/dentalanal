# 🎯 데이터 미수집 문제: 근본 원인 분석

**분석 일시**: 2026-02-20
**분석 결론**: 7개의 실제 근본 원인 발견

---

## 🔴 Critical Issues (즉시 해결 필요)

### Issue #1: 폴백 브라우저 동작 불확실성

**위치**: `base.py` 라인 33-44

```python
if cdp_url and cdp_url.startswith("wss://"):
    # Bright Data 사용
    browser = await p.chromium.connect_over_cdp(cdp_url)
else:
    # ❌ 폴백: 로컬 헤드리스 브라우저
    browser = await p.chromium.launch(headless=True)
```

**근본 원인**:
- Bright Data CDP URL이 없으면 로컬 브라우저로 폴백
- 로컬 브라우저는 Docker 컨테이너 내부에서 제한됨
- Cloud Run 환경에서 Playwright headless 브라우저 실행 불안정

**증거 1**: Dockerfile 라인 2
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
# ✅ Playwright 기본 설치됨
RUN playwright install chromium
```

**증거 2**: base.py 라인 43
```python
self.logger.info("Using Local Headless Browser (No valid CDP URL found)")
```
→ ⚠️ 로컬 브라우저 사용 중이라는 뜻!

**결과**:
```
❌ 로컬 브라우저 → Timeout 또는 빈 HTML 반환
→ naver_place.py 라인 30: "No Place data found"
→ tasks.py 라인 48: results = []
→ 데이터베이스 저장 안 됨 ❌
```

**해결책**:
```python
# 환경변수 필수 지정
BRIGHT_DATA_CDP_URL="wss://user:pass@proxy-server:port"

# 또는 로컬 테스트 시
BRIGHT_DATA_CDP_URL=""  # 로컬 브라우저 사용 (테스트 용)
```

---

### Issue #2: 네이버 Maps API 응답 구조 모호성

**위치**: `naver_place.py` 라인 23-34

```python
try:
    data = json.loads(response_text)

    if 'result' not in data or 'place' not in data['result']:
        # ❌ 구조 없으면 빈 배열 반환
        self.logger.warning(f"No Place data found in API for {keyword}")
        return []

    place_list = data['result']['place']['list']
```

**근본 원인**:
- Naver Map 공식 API는 **GraphQL 기반이 아님**
- Base URL에서 실제 응답 구조 불명확
- 로깅이 불충분해서 정확한 응답 구조를 알 수 없음

**증거 1**: BASE_URL (라인 9)
```python
BASE_URL = "https://map.naver.com/p/api/search/allSearch?query={}&type=all&searchCoord=127.027610%3B37.498095"
```
→ 문서화되지 않은 내부 API!

**증거 2**: 파싱 실패 시 로깅 (라인 30, 53)
```python
self.logger.warning(f"No Place data found in API for {keyword}")
self.logger.error(f"Failed to parse Naver Place JSON. Response len: {len(response_text)}")
```
→ 응답 길이만 로그, 실제 응답 내용 없음!

**실제 문제**:
```
응답이 옴 → JSON 파싱됨 ✅
→ 하지만 'result.place.list' 구조가 아님 ❌
→ data 구조: {"result": {"address": {...}}} 같은 다른 형식?
→ place_list = None 또는 KeyError
→ return [] ❌
```

**해결책**:
```python
# 응답 전체 로깅 추가
logger.debug(f"Full API response: {json.dumps(data, ensure_ascii=False)[:500]}")

# 구조 검증 강화
if 'result' not in data:
    logger.error(f"Missing 'result' key. Available keys: {list(data.keys())}")
    return []

result_keys = data['result'].keys() if isinstance(data['result'], dict) else []
logger.debug(f"Result structure: {result_keys}")
```

---

### Issue #3: 백그라운드 태스크 에러 소실

**위치**: `tasks.py` 라인 48-52

```python
try:
    results = asyncio.run(run_place_scraper(keyword))
except Exception as e:
    logger.error(f"Scraping failed for {keyword}: {e}")
    # ❌ 에러 상세 정보 없음
    results = []
```

**근본 원인**:
- Exception 메시지만 로깅
- 스택 트레이스 없음
- Sentry에 보고하지 않음
- 결과적으로 조용한 실패 (silent failure)

**증거**: 라인 50
```python
logger.error(f"Scraping failed for {keyword}: {e}")
# e.args[0] 정도만 로그됨
# 스택 트레이스, 파일명, 라인 번호 없음
```

**실제 시나리오**:
```
1. asyncio.run() 중 Exception 발생
   - asyncio.TimeoutError: timeout after 60s
   - playwright.async_api.TimeoutError: page.goto() timeout
   - OSError: 브라우저 연결 실패

2. logger.error(...)로만 로그
3. 사용자는 "데이터 없음" 만 봄
4. 개발자는 왜인지 모름 ❌

데이터베이스에는 기록 없음
→ 수집 시도 자체가 없던 것처럼 보임
```

**해결책**:
```python
import traceback
import logging

try:
    results = asyncio.run(run_place_scraper(keyword))
except Exception as e:
    logger.error(f"Scraping failed for {keyword}: {type(e).__name__}: {e}")
    logger.error(traceback.format_exc())  # ← 스택 트레이스

    # Sentry 보고
    if sentry_sdk:
        sentry_sdk.capture_exception(e)

    results = []
```

---

## 🟠 Major Issues (이번 주 해결)

### Issue #4: 데이터베이스 저장 에러 처리 미흡

**위치**: `tasks.py` 라인 85-92

```python
try:
    service = AnalysisService(db)
    if results:
        service.save_place_results(keyword, results, client_uuid)
    # ... 알림 추가
except Exception as e:
    logger.error(f"Saving place results or notifying failed: {e}")
    db.rollback()  # ← 트랜잭션 롤백 = 데이터 손실!
```

**근본 원인**:
- save_place_results() 실패 시 트랜잭션 롤백
- 이미 스크래핑 성공한 데이터가 모두 손실
- 사용자에게는 "완료" 알림이 간 후 실제로는 실패

**증거**:
```python
db.rollback()  # ← 모든 INSERT가 취소됨!
# Keyword, Target, DailyRank 모두 삭제됨
```

**실제 시나리오**:
```
1. scrape_place_task("임플란트") 성공 → 100개 결과
2. AnalysisService.save_place_results() 호출
3. Keyword 생성: OK ✅
4. Target 생성: OK ✅
5. DailyRank 삽입 중 제약조건 위반 (FK constraint)
   → Exception 발생
6. except: db.rollback()
7. Keyword, Target, DailyRank 모두 삭제됨! ❌
8. 사용자: "조사 완료" 알림 받음 ❌
9. 데이터베이스: 아무것도 저장 안 됨 ❌
```

**해결책**:
```python
try:
    service = AnalysisService(db)
    if results:
        service.save_place_results(keyword, results, client_uuid)
        logger.info(f"✅ Successfully saved {len(results)} ranks for {keyword}")
except Exception as e:
    logger.error(f"❌ Failed to save results: {type(e).__name__}: {e}")
    logger.error(traceback.format_exc())
    # Sentry 보고
    if sentry_sdk:
        sentry_sdk.capture_exception(e)
    # 부분 저장도 가치있음 → rollback 하지 말기
    # db.rollback() ← 제거
finally:
    db.close()
```

---

### Issue #5: Keyword와 Target의 Foreign Key 제약조건

**위치**: `analysis.py` 라인 71-95

```python
def save_place_results(self, keyword_str: str, results: List[dict], ...):
    self._save_raw_log_to_supabase(...)

    keyword = self._get_or_create_keyword(keyword_str, client_id)

    # 여기서부터 문제 시작
    for item in results:
        target = self.get_or_create_target(item.get("name"))
        # ❌ DailyRank 저장 시 어느 keyword?
```

**근본 원인**:
- DailyRank를 저장할 때 keyword_id가 필요
- 하지만 keyword 객체가 아직 flush되지 않았을 수 있음
- MySQL/PostgreSQL의 transaction isolation 때문에

**증거**: save_place_results() 구현 부분
```python
def save_place_results(self, keyword_str: str, results: List[dict], ...):
    # keyword 생성
    keyword = self._get_or_create_keyword(keyword_str, client_id)

    for item in results:
        # daily_rank 저장
        # ← keyword.id는 있는가? Flush되었는가?
```

**해결책**:
```python
def save_place_results(self, keyword_str: str, results: List[dict], ...):
    keyword = self._get_or_create_keyword(keyword_str, client_id)

    # ← keyword flush 필수
    self.db.flush()

    for item in results:
        daily_rank = DailyRank(
            id=uuid4(),
            keyword_id=keyword.id,  # ← 이제 exists
            ...
        )
        self.db.add(daily_rank)

    self.db.commit()  # ← 마지막에만 commit
```

---

### Issue #6: Naver Ads API 미분리 수집

**위치**: `naver_ad.py` - HTML 파싱 기반

```python
class NaverAdScraper(ScraperBase):
    # Naver Search (HTML 파싱)
    BASE_URL = "https://search.naver.com/search.naver?..."

    async def get_ad_rankings(self, keyword: str):
        html = await self.fetch_page_content(url, is_mobile=False)
        # ❌ 광고 파싱 전략 여러 개 시도
        ad_list = soup.select(".power_link_body .lst_type > li")
        if not ad_list:
            ad_list = soup.select("li.lst_type")
        if not ad_list:
            ad_list = soup.select(".ad_section .lst_type > li")
```

**근본 원인**:
- Naver 검색 결과 HTML 구조가 자주 변함
- 여러 선택자를 시도하지만, 모두 실패 가능
- 공식 API(Naver Ads API)가 있는데 사용 안 함

**증례**:
```python
if not results:
    self.logger.warning("No ads found. Saving HTML to debug_ad.html")
    with open("debug_ad.html", "w", encoding="utf-8") as f:
        f.write(html)
    # ← debug_ad.html은 어디에?
```

**실제 문제**:
```
1. Naver 검색 결과 페이지 가져옴
2. 파싱 시도:
   - ".power_link_body .lst_type > li" → 0개
   - "li.lst_type" → 0개 (일반 결과도 li.lst_type!)
   - ".ad_section .lst_type > li" → 0개
3. return [] ❌
4. 광고 데이터 수집 실패
```

**해결책**:
```python
# 공식 Naver Ads API 사용 필요
# 현재: naver_ads.py 에서만 쿼리 API
# 필요: 스크래핑도 공식 API 사용

# 또는 HTML 파싱 개선
# - 실제 HTML 구조 파악
# - Selenium/Playwright로 JavaScript 렌더링 후 파싱
# - 광고 섹션 ID 정확하게 추적
```

---

## 🟡 Minor Issues (다음 주)

### Issue #7: SafeScraperWrapper 에러 핸들링

**위치**: `safe_wrapper.py`

```python
class SafeScraperWrapper:
    async def run(self, method_name: str, *args, **kwargs):
        try:
            result = await method(*args, **kwargs)
            return ResponseStatus.SUCCESS
        except Exception as e:
            logger.error(f"Scraper error: {e}")
            return ResponseStatus.FAILURE
```

**문제**:
- Exception이 Sentry에 기록되지만 사용자에게는 보이지 않음
- 재시도 로직이 없음

---

## 📊 종합 진단 시나리오

### 시나리오 1: "조사시작" 클릭 → 데이터 없음

```
Frontend: SetupWizard
  ├─ "조사 시작" 클릭
  ├─ POST /api/v1/scrape/place (keyword="임플란트")
  └─ 응답: {"task_id": "...", "message": "...조사가 시작되었습니다"}

Backend: scrape.py
  ├─ trigger_place_scrape()
  ├─ _active_scraping_tasks 확인 (OK)
  ├─ background_tasks.add_task(scrape_place_task, ...)
  └─ 즉시 응답 (202 Accepted)

Background Task: tasks.py
  ├─ execute_place_sync()
  ├─ asyncio.run(run_place_scraper("임플란트"))
  │   ├─ NaverPlaceScraper.get_rankings()
  │   │   ├─ base.py: fetch_page_content()
  │   │   │   ├─ BRIGHT_DATA_CDP_URL 없음 ❌
  │   │   │   ├─ 로컬 headless 브라우저 사용
  │   │   │   ├─ Playwright headless 실행 (Cloud Run에서 불안정)
  │   │   │   └─ 빈 HTML 또는 timeout ❌
  │   │   ├─ JSON 파싱: 구조 불일치
  │   │   ├─ "No Place data found" 로그
  │   │   └─ return [] ❌
  │   └─ results = []
  ├─ if results: (False → 스킵)
  │   ├─ service.save_place_results(...) (실행 안 됨)
  │   └─ 데이터 저장 안 됨 ❌
  └─ 알림: "데이터가 발견되지 않았습니다. (0건)"

사용자 화면:
  ├─ "조사 완료" 알림 ✅ (거짓)
  ├─ 데이터베이스: 0개 레코드 ❌
  └─ 개발자: 원인 불명 ❌
```

---

## 🔧 즉시 적용 가능한 해결책 (Priority 순)

### P0: 응답 로깅 강화 (30분)
```python
# naver_place.py
logger.debug(f"API Response (first 500 chars): {response_text[:500]}")
logger.debug(f"Parsed JSON keys: {json.loads(response_text).keys() if response_text else 'empty'}")
```

### P1: 스택 트레이스 기록 (1시간)
```python
# tasks.py
import traceback
logger.error(traceback.format_exc())  # 모든 exception 블록에 추가
```

### P2: 트랜잭션 관리 개선 (2시간)
```python
# tasks.py
# rollback 제거, 부분 저장 허용
# Sentry 보고 추가
```

### P3: BRIGHT_DATA_CDP_URL 검증 (1시간)
```python
# main.py startup
if not settings.BRIGHT_DATA_CDP_URL:
    logger.warning("⚠️  BRIGHT_DATA_CDP_URL not set. Scraping will use local headless browser (unreliable)")
```

---

## 🎯 다음 액션

1. **금일 (2026-02-20)**
   - [ ] DEBUG_DATA_COLLECTION.md 검토
   - [ ] Cloud Run 로그 수집 (가능하면)
   - [ ] 코드 기반 분석 완료

2. **내일 (2026-02-21)**
   - [ ] 응답 로깅 강화 (P0)
   - [ ] 스택 트레이스 기록 (P1)
   - [ ] 테스트 데이터로 직접 검증

3. **다음 주 (2026-02-24+)**
   - [ ] 트랜잭션 관리 개선
   - [ ] 공식 API 통합 검토
   - [ ] 성능 및 안정성 모니터링

---

**작성**: 2026-02-20
**상태**: 근본 원인 분석 완료, 구체적 해결책 준비 중
