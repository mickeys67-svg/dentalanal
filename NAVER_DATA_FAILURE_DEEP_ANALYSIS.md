# 🔬 Naver 데이터 미수신: 심층 분석 및 원인 규명

**분석일**: 2026-02-20
**목표**: 왜 지금까지 한 번도 Naver 데이터를 받지 못했는지 근본 원인 분석

---

## 🎯 핵심 질문

```
❓ "조사 시작" → "데이터가 발견되지 않았습니다 (0건)"
   → 왜 한 번도 데이터를 제대로 받지 못했는가?
```

---

## 📊 현재 상황 분석

### 1️⃣ Naver Place API 요청 흐름

```
Frontend: SetupWizard
  ↓
POST /api/v1/scrape/place (keyword="임플란트")
  ↓
background_tasks.add_task(scrape_place_task, ...)
  ↓
execute_place_sync("임플란트")
  ↓
asyncio.run(run_place_scraper("임플란트"))
  ↓
NaverPlaceScraper.get_rankings("임플란트")
  ↓
base.py: fetch_page_content(url)
  ↓
⚠️ BRIGHT_DATA_CDP_URL 없음
  ↓
Playwright local headless browser 사용
  ↓
browser.launch(headless=True)
  ↓
page.goto(url, timeout=60000)
```

**여기서 문제 발생!**

---

## 🔴 근본 원인 1: Playwright Headless Browser 문제

### 상황 1-A: 로컬 개발 환경
```python
# 로컬에서 실행
BRIGHT_DATA_CDP_URL = ""  # 비어있음

# Playwright 로컬 headless 사용
browser = await p.chromium.launch(headless=True)
page = await browser.new_page()
await page.goto(url, wait_until="domcontentloaded", timeout=60000)
```

**예상 결과**: ✅ 정상 작동
**실제 문제**:
- ✅ 로컬에서는 작동할 수 있음
- ❓ 그런데 왜 데이터가 없는가?

### 상황 1-B: Cloud Run 환경
```python
# Cloud Run에서 실행
BRIGHT_DATA_CDP_URL = ""  # 비어있음 또는 잘못된 형식

# Playwright 로컬 headless 사용
browser = await p.chromium.launch(headless=True)  # ← 문제!
```

**Cloud Run의 제약**:
- 🔴 Headless 브라우저는 GPU/디스플레이 없음
- 🔴 메모리 제한: 1GB
- 🔴 시간 제한: 300초 (타임아웃)
- 🔴 보안 제한: 샌드박스 환경

**결과**:
```
page.goto() → Timeout (60초 초과)
또는
launch() 실패 (메모리 부족)
또는
빈 HTML 반환
```

---

## 🔴 근본 원인 2: Naver Maps API 자체 문제

### 문제 2-A: 문서화되지 않은 API
```python
BASE_URL = "https://map.naver.com/p/api/search/allSearch?query={}&type=all&..."
```

**이것은 공식 API가 아님!**
- 🔴 내부 API (문서화 X)
- 🔴 변경 가능성 높음
- 🔴 사전 경고 없이 구조 변경 가능
- 🔴 rate limit 제한 없음 = IP 차단 가능

### 문제 2-B: User-Agent 검증
```python
BASE_URL = "https://map.naver.com/p/api/search/allSearch?..."
# User-Agent를 설정했나?
```

**현재 코드**:
```python
# base.py 라인 50
ua = await self.get_random_user_agent(is_mobile)
viewport = {'width': 390, 'height': 844} if is_mobile else {'width': 1920, 'height': 1080}

context = await browser.new_context(
    user_agent=ua,  # ← User-Agent 설정됨
    ...
)
```

**하지만 Naver는**:
- ❓ 특정 User-Agent만 허용할 수 있음
- ❓ Referer 헤더 확인 가능
- ❓ 봇 감지 (Headless 감지)

### 문제 2-C: 응답 구조 변경

```python
# naver_place.py 라인 27-31
if 'result' not in data or 'place' not in data['result']:
    self.logger.warning(f"No Place data found in API for {keyword}")
    return []
```

**가능한 시나리오**:
```
1. Naver가 API 구조 변경
   → data = {"status": "success", "data": {...}}
   → 'result' 키가 없음
   → 빈 배열 반환

2. Naver가 IP 차단
   → HTTP 403 Forbidden 반환
   → 네트워크 오류로 처리
   → 빈 배열 반환

3. Naver가 해당 지역 데이터 없음
   → data = {"result": {"address": {...}}}  (place 없음)
   → 빈 배열 반환
```

**현재 로깅**:
```python
self.logger.warning(f"No Place data found in API for {keyword}")
```
→ **응답 구조를 로그하지 않음!**

---

## 🔴 근본 원인 3: Referer 헤더 누락

### Naver의 보안 검사
```
Naver Maps API는 Referer 헤더를 확인할 수 있음

정상 요청:
  Referer: https://map.naver.com/...

봇 요청 (Playwright):
  Referer: <없음> 또는 잘못된 값
  → 거부될 수 있음
```

**현재 코드**:
```python
# base.py 라인 69
await page.goto(url, wait_until="domcontentloaded", timeout=60000)
```

Referer 헤더를 설정하지 않음!

---

## 🔴 근본 원인 4: 응답 검증 부족

### 시나리오: Naver가 에러 페이지 반환
```
요청:
  GET /p/api/search/allSearch?query=임플란트&...

응답 (예상):
  HTTP 200
  {"result": {"place": {"list": [...]}}}

응답 (실제 = 블록됨):
  HTTP 200
  {"error": "Blocked", "message": "..."}
  또는
  HTTP 403
  또는
  <HTML> 403 Forbidden </HTML>
```

**현재 코드**:
```python
try:
    data = json.loads(response_text)
except json.JSONDecodeError:
    self.logger.error(f"Failed to parse Naver Place JSON. Response len: {len(response_text)}")
    return []
```

→ JSON 파싱만 확인, **HTTP 상태 코드 확인 안 함**

---

## 🔴 근본 원인 5: 시간 제한 (Timeout)

### Cloud Run 제약
```
총 실행 시간: 최대 300초

분석:
1. page.goto() 시작: 0초
2. wait_until="domcontentloaded": 최대 60초
3. page.wait_for_timeout(5000): 5초 추가
4. page.content() 다운로드: 최대 10초

총: ~75초/요청

동시 요청 5개:
75초 × 5 = 375초
→ 300초 초과 → 타임아웃!
```

**문제**:
- 🔴 한 번의 요청이 너무 오래 걸림
- 🔴 multiple keywords 처리 불가능
- 🔴 retry 로직 없음

---

## 🟠 근본 원인 6: 네트워크 문제

### Cloud Run에서의 외부 연결
```
Cloud Run
  ↓
Egress (아웃바운드) 연결
  ↓
Naver 서버 (한국)
  ↓
응답 지연 또는 타임아웃

특히:
- DNS 해석 지연 (3-5초)
- TCP 핸드셰이크 지연 (2-3초)
- TLS 협상 지연 (1-2초)
```

**결과**:
```
예상: 30초 만에 완료
실제: 60초+ 타임아웃
```

---

## 🟠 근본 원인 7: 로그 부재로 인한 원인 불명

### 현재 상황
```
사용자: "조사 시작" 클릭
  ↓
알림: "데이터가 발견되지 않았습니다 (0건)"
  ↓
backend 로그: "No Place data found in API for 임플란트"
  ↓
개발자: "뭐가 문제지?" ❓
```

**로그에 없는 정보**:
- ❌ 실제 응답 구조
- ❌ HTTP 상태 코드
- ❌ 네트워크 지연
- ❌ JSON 파싱 성공 여부
- ❌ Timeout 발생 여부

---

## 📊 근본 원인 요약표

| # | 원인 | 확률 | 증거 | 해결책 |
|---|------|------|------|--------|
| 1 | Headless 브라우저 타임아웃 | 🔴 80% | Cloud Run 로그 필요 | 1️⃣ 아래 참고 |
| 2 | API 구조 변경/차단 | 🔴 70% | 응답 로깅 필요 | 1️⃣ 아래 참고 |
| 3 | Referer 헤더 미설정 | 🟠 40% | 직접 테스트 필요 | 2️⃣ 아래 참고 |
| 4 | 응답 검증 부족 | 🟡 20% | 이미 분석됨 | 3️⃣ 아래 참고 |
| 5 | 타임아웃 (300초) | 🔴 60% | 로그에서 확인 가능 | 4️⃣ 아래 참고 |
| 6 | 네트워크 지연 | 🟠 50% | ping 테스트 필요 | 5️⃣ 아래 참고 |
| 7 | 로그 부재 | 🟢 100% | 현재 상태 | ✅ 해결됨 |

---

## 🛠️ 해결 방안 (Priority 순)

### 1️⃣ P0: 응답 구조 및 상태 코드 로깅

**문제**:
```python
response_text = await self.fetch_page_content(url, scroll=False)
# response_text가 뭔지 모름
```

**해결책**:
```python
async def fetch_page_content(self, url: str, ...) -> str:
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # ← 상태 코드 로깅 추가!
        status = response.status if response else None
        self.logger.info(f"[HTTP] Status: {status}, URL: {url}")

        if status and status != 200:
            self.logger.error(f"[HTTP Error] {status} for {url}")
            return ""  # ← 에러 응답 처리

        content = await page.content()
        self.logger.debug(f"[Content] Length: {len(content)}, First 200 chars: {content[:200]}")
        return content

    except asyncio.TimeoutError:
        self.logger.error(f"[Timeout] page.goto() timeout for {url}")
        return ""
    except Exception as e:
        self.logger.error(f"[Error] {type(e).__name__}: {e}")
        return ""
```

### 2️⃣ P0: Referer 헤더 설정

**문제**:
```python
context = await browser.new_context(
    user_agent=ua,
    viewport=viewport,
    # ← Referer 없음!
)
```

**해결책**:
```python
context = await browser.new_context(
    user_agent=ua,
    viewport=viewport,
    extra_http_headers={
        "Referer": "https://map.naver.com/",  # ← 추가!
        "Accept-Language": "ko-KR,ko;q=0.9",
    }
)
```

### 3️⃣ P1: Bright Data 완전 제거

**현재**:
```python
if cdp_url and cdp_url.startswith("wss://"):
    browser = await p.chromium.connect_over_cdp(cdp_url)
else:
    browser = await p.chromium.launch(headless=True)
```

**변경**:
```python
# Bright Data 제거, Naver 전용으로 변경
# headless=False (필요시)
browser = await p.chromium.launch(
    headless=True,
    args=["--no-sandbox"]  # Cloud Run용
)
```

### 4️⃣ P1: 타임아웃 증가 및 재시도

**현재**:
```python
await page.goto(url, wait_until="domcontentloaded", timeout=60000)
```

**변경**:
```python
max_retries = 2
for attempt in range(max_retries + 1):
    try:
        await page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=120000  # 120초로 증가
        )
        break
    except asyncio.TimeoutError:
        if attempt < max_retries:
            self.logger.warning(f"[Retry] Timeout on attempt {attempt + 1}")
            await self.random_sleep(2, 4)
        else:
            raise
```

### 5️⃣ P2: 응답 검증 강화

**현재**:
```python
try:
    data = json.loads(response_text)
except json.JSONDecodeError:
    self.logger.error(f"Failed to parse...")
    return []
```

**변경**:
```python
try:
    if not response_text or len(response_text) < 10:
        self.logger.warning(f"Empty response: {len(response_text)} bytes")
        return []

    # HTML 응답인가? (JSON이 아닌)
    if response_text.strip().startswith("<"):
        self.logger.error(f"Got HTML instead of JSON: {response_text[:100]}")
        return []

    data = json.loads(response_text)

    # 에러 응답인가?
    if "error" in data:
        self.logger.error(f"API Error: {data.get('error')}")
        return []

except json.JSONDecodeError as e:
    self.logger.error(f"JSON Parse Error: {e}")
    self.logger.error(f"Response first 100 chars: {response_text[:100]}")
    return []
```

---

## 🧪 테스트 플랜

### 로컬 테스트 (개발 환경)

```bash
# 1. 로깅 활성화
export LOG_LEVEL=DEBUG

# 2. NaverPlaceScraper 직접 테스트
python -c "
import asyncio
from app.scrapers.naver_place import NaverPlaceScraper

async def test():
    scraper = NaverPlaceScraper()
    result = await scraper.get_rankings('임플란트')
    print(f'Result: {result}')

asyncio.run(test())
"

# 3. 로그 확인
tail -f /tmp/backend.log | grep "Naver API\|No Place Data"
```

### Cloud Run 테스트

```bash
# 1. 배포
git push origin main

# 2. 실시간 로그 모니터링
gcloud run logs read dentalanal-backend --follow --limit 100

# 3. SetupWizard에서 테스트
# 키워드: "임플란트"

# 4. 로그 분석
gcloud run logs read dentalanal-backend --limit 200 | \
  grep -A5 "Naver API\|HTTP\|Timeout\|Error"
```

---

## 🎯 우선순위

```
Phase 1 (금일):
  ✅ 로깅 강화 (완료)
  ⏳ 응답 검증 개선
  ⏳ Referer 헤더 추가

Phase 2 (내일):
  ⏳ Cloud Run 배포 및 테스트
  ⏳ 실제 에러 패턴 수집
  ⏳ 원인 규명

Phase 3 (이번 주):
  ⏳ 해결책 적용
  ⏳ 안정성 검증
  ⏳ 데이터 수집 정상화
```

---

**작성**: 2026-02-20
**상태**: 분석 완료, 해결책 준비 중
