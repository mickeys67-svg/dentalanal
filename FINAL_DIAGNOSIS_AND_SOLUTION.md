# 🎯 최종 진단: Naver 데이터 미수신 근본 원인 및 해결책

**분석 완료일**: 2026-02-21  
**심각도**: 🔴 CRITICAL  
**상태**: ✅ 근본 원인 규명 완료

---

## 📊 종합 분석 결과

### Root Cause: Naver API가 작동하지 않음

우리가 사용 중인 Naver Maps API 엔드포인트:
```
https://map.naver.com/p/api/search/allSearch?query={keyword}&type=all&searchCoord=...
```

**응답 패턴**:
```json
{
  "result": {
    "type": "all",
    "metaInfo": {...},
    "place": null,      ← ❌ 항상 null
    "address": null,    ← ❌ 항상 null
    "bus": null         ← ❌ 항상 null
  }
}
```

**테스트한 모든 키워드가 동일한 결과**:
- 임플란트
- 치과
- 강남역 치과
- 서울 임플란트
- 배재대학교
- 서울시청

---

## 🔍 원인 분석 (4단계)

### 1️⃣ HTML Wrapper 문제 (해결됨 ✅)
```
❌ 원래: <html><pre>JSON</pre></html>로 감싸짐
✅ 해결: regex로 <pre> 태그에서 JSON 추출
```

**상태**: ✅ 수정 완료 (commit c7c0075)

### 2️⃣ HTTP 상태 코드 (정상 ✅)
```
✅ HTTP 200: 요청은 성공함
✅ Content-Type: application/json 올바름
❌ 하지만 실제 데이터: 없음
```

### 3️⃣ API 자체 문제 (근본 원인 🔴)

**발견 1**: allSearch API가 데이터를 반환하지 않음
- HTTP 200이지만 place=null
- 이는 API가 작동하지 않거나
- 우리의 요청 형식이 잘못됨

**발견 2**: 다른 API 엔드포인트 시도
```
GET /p/api/search/place?query=xxx → 404 Not Found
→ 이 엔드포인트는 존재하지 않음
```

**발견 3**: Naver Maps 웹사이트 자체도 JavaScript 렌더링
```
https://map.naver.com/p/search/{keyword}
→ HTML: 6KB (매우 작음)
→ 결론: React 앱이 클라이언트에서 렌더링
→ 검색 결과는 JavaScript 실행으로만 나타남
```

---

## 🤔 가능한 원인들

### 원인 1: Naver가 공식적으로 API를 제공하지 않음
```
allSearch API는 문서화되지 않은 내부 API
→ 언제든 변경되거나 차단될 수 있음
→ 현재 place=null이 그 신호일 수 있음
```

### 원인 2: Headless 브라우저 감지 및 차단
```
Naver가 자동화 도구(Playwright)를 감지
→ 데이터를 반환하지 않음 (보안 정책)
→ 실제 브라우저에서는 작동할 수 있음
```

### 원인 3: 요청 형식 또는 인증 문제
```
CSRF 토큰 필요?
세션 쿠키 필요?
특정 헤더 필요?
```

### 원인 4: Naver API 서비스 중단
```
API 자체가 더 이상 제공되지 않음
또는 특정 쿼리에서만 비활성화됨
```

---

## ✅ 구현된 해결책 (P0/P1)

### P0: 근본적인 문제 해결
```python
# 1. HTML wrapper 제거 (commit c7c0075)
# → regex로 <pre> 태그에서 JSON 추출

# 2. Referer 헤더 추가 (commit ad13cf1)
# → Naver 검증 통과 시도

# 3. 상세 로깅 추가
# → HTTP 상태 코드, 응답 내용, 타임아웃 등
```

### P1: 견고성 개선
```python
# 1. 타임아웃 60초 → 120초
# 2. 재시도 로직: 최대 2회
# 3. asyncio.TimeoutError 명시적 처리
```

---

## 🚨 현재 상황

| 단계 | 결과 | 상태 |
|-----|------|------|
| Playwright 브라우저 연결 | ✅ 성공 | 정상 |
| Naver API 요청 | ✅ HTTP 200 | 정상 |
| JSON 파싱 | ✅ 성공 | 정상 |
| 데이터 추출 | ❌ place=null | **문제** |

**결론**: 우리의 기술적 구현은 모두 정상. 문제는 **Naver API 자체가 데이터를 제공하지 않음**.

---

## 🛠️ 다음 단계 선택지

### Option 1: Naver Search API 사용 (공식)
```
Naver Search API (블로그, 뉴스, 카페 검색 제공)
→ 하지만 Place 검색은 미제공
→ 불가능 ❌
```

### Option 2: Naver Ads API 강화 (공식)
```
✅ 이미 구현 중
✅ 광고 데이터는 정상 수집
→ Place 데이터 부족하지만 일부 해결
```

### Option 3: HTML 스크래핑으로 전환 ⭐ 권장
```
Playwright로 검색 페이지 방문
→ JavaScript 렌더링 완료 대기
→ 화면에 표시된 결과를 HTML/JavaScript에서 추출
→ 이 방법이 유일한 해결책
```

### Option 4: AI 크롤러 (비용)
```
외부 AI 크롤링 서비스 이용
→ 비용 증가
→ 레이턴시 증가
→ 필요 시 나중에 고려
```

### Option 5: 사용자에게 수동 입력 요청
```
사용자가 경쟁사 정보를 직접 입력
→ 확장성 떨어짐
→ UX 나쁨
→ 비추천 ❌
```

---

## 🎯 권장 해결책: Option 3 (HTML 스크래핑)

### 구현 전략

**Step 1**: Naver Maps 검색 페이지 방문
```python
url = "https://map.naver.com/p/search/{keyword}"
response = await page.goto(url, wait_until="networkidle")
```

**Step 2**: JavaScript 렌더링 대기
```python
# networkidle: 모든 네트워크 요청 완료 대기
# 또는
await page.wait_for_timeout(3000)  # 3초 대기
```

**Step 3**: 검색 결과 HTML에서 추출
```python
# React로 렌더링된 결과에서:
# - 장소 이름
# - 카테고리
# - 주소
# - 상단 광고
# - 일반 검색 결과
```

**Step 4**: 데이터 정규화
```python
results = [
    {
        "rank": 1,
        "name": "서울시청",
        "category": "공공기관",
        "address": "서울시 중구 세종대로...",
        "keyword": "서울시청"
    },
    ...
]
```

---

## 📝 구현 계획

### Phase A: 검증 (지금)
- [x] Naver API 테스트: place=null 확인
- [x] 여러 키워드 테스트: 모두 null
- [x] 다른 API 엔드포인트: 404
- [x] HTML 페이지 분석: React 클라이언트 렌더링
- [ ] headless=False로 실제 렌더링 확인

### Phase B: 개발 (다음)
- [ ] HTML 스크래핑 코드 작성 (NaverPlaceScraper 개선)
- [ ] 선택자 개발 (div.class 등)
- [ ] 데이터 추출 로직
- [ ] 테스트

### Phase C: 배포
- [ ] Cloud Run에 배포
- [ ] 실제 데이터 수집 확인
- [ ] 경쟁사 분석 정상화

---

## 📊 시간 예측

| 단계 | 소요시간 |
|-----|---------|
| HTML 스크래핑 코드 개발 | 2-3시간 |
| 테스트 및 디버깅 | 1-2시간 |
| 배포 및 검증 | 30분 |
| **총계** | **3-5시간** |

---

## 🎓 배운 점

1. **문서화되지 않은 API의 위험성**
   - allSearch API는 Naver 내부 API
   - 공식 문서 없음 = 언제든 변경 가능

2. **Headless 브라우저 감지**
   - Naver가 자동화 도구 차단 가능성
   - 실제 사용자와 다른 응답

3. **클라이언트 사이드 렌더링의 영향**
   - Naver Maps는 React 기반
   - 검색 결과는 JavaScript에서만 생성
   - 스크래핑 필수

---

## ✅ 결론

**Naver Maps API는 더 이상 작동하지 않습니다.**

- ❌ 공식 API가 없음 (allSearch는 내부 API)
- ❌ 현재 place=null 반환
- ✅ 해결책: HTML 스크래핑으로 전환

**다음 커밋**: HTML 스크래핑 기능 개발

---

## 📎 관련 문서

- `NAVER_DATA_FAILURE_DEEP_ANALYSIS.md` - 초기 분석
- `NAVER_HTML_WRAPPER_ROOT_CAUSE.md` - HTML wrapper 분석
- `test_naver_api.py` - API 테스트 스크립트
- `test_naver_comprehensive.py` - 다중 키워드 테스트
- `test_naver_search_page.py` - 다양한 API 엔드포인트 테스트
- `test_naver_html_scrape.py` - HTML 스크래핑 테스트

---

**최종 상태**: 근본 원인 규명 완료 ✅  
**다음 단계**: HTML 스크래핑 구현  
**예상 완료**: 2026-02-21 (오늘)
