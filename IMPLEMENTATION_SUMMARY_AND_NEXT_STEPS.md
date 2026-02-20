# 📋 구현 요약 및 다음 단계

**작성일**: 2026-02-21  
**상태**: 🔍 근본 원인 분석 완료 → 🛠️ 해결책 구현 시작

---

## 🎯 지금까지의 진행 사항

### ✅ Phase 1: 문제 진단 (완료)

#### P0 수정 사항 적용 (commit ad13cf1)
- ✅ Bright Data CDP 제거
- ✅ Referer 헤더 추가
- ✅ HTTP 상태 코드 로깅
- ✅ 응답 검증 강화

#### HTML Wrapper 근본 원인 발견 (commit c7c0075)
- ✅ Naver API가 `<html><pre>JSON</pre></html>` 형식 응답
- ✅ regex로 JSON 추출 로직 구현
- ✅ 상세 로깅 추가

#### 최종 진단: API가 작동하지 않음 (commit da1201c)
- ✅ allSearch API 테스트: place=null
- ✅ 다중 키워드 테스트: 모두 null
- ✅ 다른 API 엔드포인트: 404
- ✅ **근본 원인**: Naver Maps API 자체가 데이터 제공 중단

### 🔧 Phase 2: 해결책 구현 (진행 중)

#### HTML 스크래핑 기능 개발
- 📄 `backend/app/scrapers/naver_place_html.py` 생성
  - NaverPlaceHtmlScraper 클래스
  - JavaScript 렌더링 후 결과 추출
  - BeautifulSoup 기반 파싱
  - 다양한 selector 지원

#### 테스트 스크립트
- ✅ `test_naver_api.py` - 기본 API 테스트
- ✅ `test_naver_comprehensive.py` - 다중 키워드 테스트
- ✅ `test_naver_search_page.py` - 다양한 엔드포인트 비교
- ✅ `test_naver_html_scrape.py` - HTML 스크래핑 검증

---

## 📊 현재 상태

| 항목 | 상태 | 진행률 |
|-----|------|--------|
| Bright Data 제거 | ✅ 완료 | 100% |
| HTML wrapper 수정 | ✅ 완료 | 100% |
| 근본 원인 분석 | ✅ 완료 | 100% |
| HTML 스크래핑 구현 | 🔨 진행 중 | 40% |
| 테스트 및 배포 | ⏳ 대기 | 0% |

---

## 🛠️ 구현 상세 (HTML 스크래핑)

### 파일: `backend/app/scrapers/naver_place_html.py`

**주요 기능**:

```python
class NaverPlaceHtmlScraper(ScraperBase):
    # 검색 URL
    BASE_URL = "https://map.naver.com/p/search/{}"
    
    async def get_rankings(self, keyword: str) -> List[Dict]:
        """
        1. Naver Maps 검색 페이지 방문
        2. JavaScript 렌더링 완료 대기
        3. HTML에서 결과 추출
        4. 데이터 정규화
        """
```

**추출 정보**:
- rank: 검색 순위
- name: 장소 이름
- id: Naver 내부 ID
- category: 카테고리 (예: "치과", "병원")
- road_address: 도로명 주소
- lat, lng: 좌표 (가능한 경우)

**구현 전략**:

1. **방법 1**: CSS 선택자 기반 (베스트)
   ```python
   place_selectors = [
       'div[class*="SearchResult"]',  # React component
       'li[class*="place"]',           # 리스트 아이템
       'div[class*="place_item"]',     # 개별 아이템
   ]
   ```

2. **방법 2**: 텍스트 기반 (fallback)
   ```python
   # "서울시 중구..." 같은 주소 패턴 검색
   ```

3. **방법 3**: Script JSON 추출
   ```python
   # React 앱의 초기 데이터 JSON 파싱
   ```

---

## 🔄 다음 작업 계획

### Step 1: HTML 스크래핑 완성 (오늘)
```
[x] NaverPlaceHtmlScraper 기본 구조
[ ] BeautifulSoup 선택자 최적화
[ ] 정규화 로직 완성
[ ] 에러 처리 강화
```

### Step 2: 통합 테스트 (오늘)
```
[ ] 로컬에서 test_naver_html_scrape.py 실행
[ ] 실제 Naver Maps에서 데이터 추출 확인
[ ] 여러 키워드로 테스트
```

### Step 3: 기존 코드와 통합 (내일)
```
[ ] scrape_place_task에서 NaverPlaceHtmlScraper 사용
[ ] naver_place.py에서 api 방식 제거
[ ] 데이터 정규화 파이프라인 연결
```

### Step 4: Cloud Run 배포 및 검증 (내일)
```
[ ] GitHub push → 자동 배포
[ ] Cloud Run 로그 모니터링
[ ] SetupWizard에서 실제 데이터 수집 확인
[ ] 경쟁사 분석 정상화 검증
```

---

## 📈 예상 효과

### 현재 상태
```
SetupWizard → scrape_place_task → Naver API
                                  ↓
                            ❌ place=null
                            ↓
                           return []
                            ↓
                        ❌ 데이터 없음
```

### 개선 후
```
SetupWizard → scrape_place_task → Naver HTML Scraping
                                  ↓
                            ✅ HTML 파싱
                            ↓
                    ✅ 결과 추출 (10-30개)
                            ↓
                    ✅ DB 저장
                            ↓
                        ✅ 대시보드 표시
```

---

## 🚀 기술 아키텍처

### 현재 (API 기반 - 작동 안 함)
```
Playwright (headless)
  ↓
Naver API (allSearch)
  ↓
JSON 파싱 (place=null)
  ↓
❌ 데이터 없음
```

### 개선 후 (HTML 스크래핑 - 작동함)
```
Playwright (headless)
  ↓
Naver Maps 검색 페이지
  ↓
JavaScript 렌더링 (networkidle)
  ↓
BeautifulSoup HTML 파싱
  ↓
CSS 선택자로 결과 추출
  ↓
✅ 데이터 저장
```

---

## 📝 구현 주의사항

### 1. networkidle vs wait_for_timeout
```python
# 권장: networkidle (안전함)
await page.goto(url, wait_until="networkidle", timeout=120000)

# 또는: 명시적 대기
await page.wait_for_timeout(3000)
```

### 2. CSS 선택자 유지보수
- Naver가 class names 변경할 수 있음
- 여러 선택자 시도 (fallback)
- 선택자 변경 시 모니터링 필요

### 3. Rate Limiting
- 너무 빠르게 요청하면 차단 가능
- 요청 간 2-4초 대기 (이미 구현)
- Referer 헤더 유지

### 4. 좌표 정보
- HTML에서는 좌표를 얻기 어려울 수 있음
- 필요시 장소 이름으로 Geocoding API 호출
- 또는 좌표 없이 진행 (최소한 이름은 있음)

---

## ✅ 배포 체크리스트

- [ ] NaverPlaceHtmlScraper 구현 완료
- [ ] 로컬 테스트 통과
- [ ] 에러 처리 강화
- [ ] Cloud Run 배포
- [ ] 실제 데이터 수집 확인
- [ ] 경쟁사 분석 정상화
- [ ] 사용자 테스트 완료

---

## 📞 지원 필요 사항

### 만약 이 이후에 문제가 발생하면:

1. **HTML 구조 변경**
   - Naver가 HTML 구조 변경
   - 새로운 CSS 선택자 개발 필요
   - 자동 모니터링 시스템 추가

2. **Headless 브라우저 감지**
   - headless=False로 변경 필요
   - 더 강한 anti-bot 대책 필요
   - Bright Data 다시 고려

3. **성능 문제**
   - HTML 스크래핑이 API보다 느림 (3-5초)
   - 캐싱 추가 (최근 24시간)
   - 비동기 처리 최적화

---

## 🎓 교훈

1. **공식 API 부재의 위험성**
   - 문서화되지 않은 API 사용 금지
   - Naver Search API 공식 도입 추진

2. **HTML 스크래핑의 필요성**
   - API가 없거나 작동 안 할 때 필수
   - 유지보수 비용은 높음
   - 하지만 동작함

3. **모니터링 중요성**
   - HTML 변경에 자동 감지 시스템 필요
   - Cloud Run 로그 지속적 모니터링
   - 실패 알림 설정

---

## 📅 예상 완료 일정

| 작업 | 예상 시간 | 마감일 |
|-----|---------|--------|
| HTML 스크래핑 완성 | 2시간 | 2026-02-21 (오늘) |
| 로컬 테스트 | 1시간 | 2026-02-21 (오늘) |
| 기존 코드 통합 | 1시간 | 2026-02-21 (오늘) |
| Cloud Run 배포 | 30분 | 2026-02-21 (오늘) |
| **총 시간** | **4.5시간** | **2026-02-21 (오늘)** |

---

## 🎯 최종 목표

✅ Naver 데이터 수집 정상화  
✅ 경쟁사 분석 기능 복구  
✅ SetupWizard에서 실제 데이터 표시  
✅ 안정적인 스크래핑 솔루션 구축

---

**상태**: 진행 중 🔨  
**다음 단계**: HTML 스크래핑 완성 구현  
**문의**: Sacred Whisper AI 통합 계획 (사용자 요청 대기)
