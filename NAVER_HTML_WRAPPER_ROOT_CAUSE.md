# 🔴 네이버 데이터 미수신 근본 원인: HTML Wrapper 문제

**발견일**: 2026-02-21  
**심각도**: 🔴 CRITICAL - 지금까지 데이터를 받지 못한 이유

---

## 🎯 발견 내용

### 문제: Naver Maps API 응답이 HTML `<pre>` 태그로 감싸짐

**예상 응답**:
```json
{"result":{"type":"all","metaInfo":{...},"place":{"list":[...]}}}
```

**실제 응답**:
```html
<html>
  <head>...</head>
  <body>
    <pre>{"result":{"type":"all","metaInfo":{...},"place":{...}}}</pre>
  </body>
</html>
```

### 결과

| 단계 | 상황 |
|-----|-----|
| 1. Playwright 브라우저 | URL 접근 성공 (HTTP 200) ✅ |
| 2. `page.content()` | **HTML 전체 반환** (JSON이 아님) ❌ |
| 3. `json.loads(html)` | **파싱 실패** (JSON이 아니기 때문) ❌ |
| 4. Exception catch | `[]` 반환 → 데이터 없음 ❌ |

---

## 🔍 상세 분석

### HTTP 응답 헤더
```
Content-Type: application/json; charset=utf-8  ← JSON이라고 명시!
Content-Length: 346 bytes
Access-Control-Allow-Origin: https://map.naver.com
```

### 실제 응답 Body
```
<html><head>...</head><body><pre>JSON_CONTENT</pre></body></html>
```

**矛盾점**: 
- ✅ Content-Type은 JSON
- ❌ 하지만 Body는 HTML
- 🤔 왜 이런 구조일까?

### 가능한 원인들

1. **Naver 보안 정책** - Playwright 같은 자동화 도구 감지 후 의도적으로 HTML 감싸기?
2. **브라우저 렌더링** - JavaScript 실행 결과가 HTML로 변환?
3. **CDN 캐싱** - Naver CDN에서 HTML 래핑?
4. **개발 중인 기능** - 아직 완성되지 않은 API?

---

## 🔧 구현된 수정 사항

### 파일: `backend/app/scrapers/base.py`

**추가 코드** (fetch_page_content 메서드):

```python
# HTML wrapper에서 JSON만 추출
if content.strip().startswith("<"):
    logger.warning(f"[HTML Wrapper Detected] Extracting JSON from HTML...")
    try:
        # <pre> 태그에서 JSON 추출
        import re
        match = re.search(r'<pre>(.*?)</pre>', content, re.DOTALL)
        if match:
            json_content = match.group(1)
            logger.info(f"[JSON Extracted] Length: {len(json_content)} bytes")
            return json_content
        else:
            logger.error(f"[HTML Parse Failed] Could not find <pre> tag in HTML")
            return ""
    except Exception as e:
        logger.error(f"[HTML Extract Error] {e}")
        return ""
```

---

## 📊 테스트 결과

### 테스트 1: HTML Wrapper 제거 확인

**스크립트**: `test_naver_api.py`

**결과**:
```
Content Length: 501 bytes (HTML 포함)
↓ [HTML Wrapper Detected]
↓ [JSON Extracted] Length: 338 bytes
↓ [JSON Parsing] SUCCESS ✅
```

**결론**: HTML wrapper 제거 후 JSON 파싱 성공!

---

### 테스트 2: 여러 키워드 테스트

**스크립트**: `test_naver_comprehensive.py`

**결과**:
```
✅ [임플란트]     NO DATA (place=None)
✅ [치과]         NO DATA (place=None)
✅ [강남역 치과]   NO DATA (place=None)
✅ [서울 임플란트] NO DATA (place=None)
✅ [배재대학교]   NO DATA (place=None)
✅ [서울시청]     NO DATA (place=None)
```

**중요한 발견**: 
- ✅ HTML wrapper 문제는 해결됨
- ✅ JSON 파싱도 성공함
- ❌ 하지만 **"place": null** - 실제 데이터가 없음

**새로운 의문**: 
- 모든 키워드에서 place=null인 이유?
- Naver가 headless 브라우저 요청을 차단?
- 아니면 실제로 데이터가 없는 건가?

---

## 🔬 다음 조사 계획

### 1. Headless 감지 테스트
```python
# headless=False로 실행하면 데이터가 오는가?
browser = await p.chromium.launch(headless=False)
```

### 2. 실제 웹브라우저에서 확인
```
URL을 직접 브라우저에서 방문
→ 개발자 도구 Network 탭에서 응답 확인
→ place 데이터가 있는가?
```

### 3. 다른 API 엔드포인트 시도
```
1. /p/api/search/allSearch (현재 - place=null)
2. /p/api/search/place (place 전용?)
3. 다른 쿼리 파라미터?
```

---

## 📝 배포 상태

**커밋**: `ad13cf1` - HTML wrapper 추출 로직 추가  
**배포**: ✅ Cloud Run에 배포 예정

**변경 파일**:
- `backend/app/scrapers/base.py` - HTML wrapper 처리 추가

---

## ⚠️ 현재 문제점 정리

| # | 문제 | 상태 | 원인 |
|---|-----|------|-----|
| 1 | HTML wrapper로 JSON 감싸짐 | ✅ 해결됨 | Naver API 응답 형식 |
| 2 | 모든 키워드에서 place=null | ❌ 미해결 | 미상 - 조사 필요 |
| 3 | Headless 브라우저 감지 가능성 | ⏳ 검토 예정 | 보안 측정 |

---

## 🎯 결론

**HTML wrapper는 해결했으나, place=null 문제는 아직 남음**

다음 단계:
1. headless=False 테스트
2. 실제 브라우저에서 확인
3. 필요시 다른 API 엔드포인트 시도
