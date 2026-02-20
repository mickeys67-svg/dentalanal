# Phase 2 기능 검증 가이드

## 📌 Overview

Phase 2-1, 2-2, 2-3을 모두 구현하고 배포했습니다. 이제 실제 환경에서 동작을 검증해야 합니다.

**배포 상태**: ✅ GitHub Actions 배포 진행 중 (commit: 62d376f)

---

## 🎯 Phase 2 검증 목표

### Phase 2-1: 에러 핸들링 ✓
- ✅ 스크래핑 실패 시 백엔드 에러 메시지가 UI에 표시됨
- ✅ 특정 에러 메시지 (상세 정보) 표시
- ✅ 재시도 버튼으로 에러 상태 초기화

### Phase 2-2: 동적 폴링 ✓
- ✅ 고정 2초 대기 → 500ms-3초 동적 폴링으로 변경
- ✅ 폴링은 최대 30초까지 진행
- ✅ 데이터 수신 시 즉시 표시 (폴링 중단)

### Phase 2-3: 동시 요청 방지 ✓
- ✅ 같은 키워드로 중복 스크래핑 시 409 Conflict 반환
- ✅ 사용자에게 "이미 진행 중"이라는 메시지 표시

---

## 🔧 테스트 환경 준비

### 1단계: 테스트 데이터 생성

배포가 완료되면 다음 API를 호출하여 테스트 데이터를 생성합니다:

```bash
# 프로덕션 환경
POST https://dentalanal-864421937037.us-west1.run.app/api/v1/status/dev/seed-test-data

# 응답 예시:
{
  "status": "SUCCESS",
  "message": "테스트 데이터가 성공적으로 생성되었습니다.",
  "client_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "details": {
    "agency": "D-MIND 대행사",
    "client": "A 치과",
    "keywords": ["임플란트", "치아교정", "강남역치과"],
    "platforms": ["NAVER_AD", "NAVER_PLACE", "NAVER_VIEW"],
    "sample_ranks": "지난 3일치 데이터 (테스트용)"
  }
}
```

**응답에서 `client_id` 기억해두기!** → 이 ID로 SetupWizard 테스트

### 2단계: 프로덕션 배포 확인

대략 5-10분 후 다음 URL에서 새 이미지가 배포되었는지 확인:

```
https://dentalanal-864421937037.us-west1.run.app/health
```

응답:
```json
{"status": "ok"}
```

---

## 🧪 테스트 시나리오

### Scenario 1: 정상 폴링 (Phase 2-2 검증)

**목표**: 500ms-3초 간 폴링하다가 데이터가 표시되는 것 확인

**단계**:
1. 애플리케이션 접속
2. 새 프로젝트 생성 시작 (또는 기존 프로젝트에서 "실시간조사시작")
3. SetupWizard Step 3에서:
   - 분석 키워드: `임플란트`
   - 분석 대상: `NAVER_PLACE` (네이버 플레이스)
4. 스크래핑 시작 버튼 클릭

**기대 동작**:
```
발생 순서:
┌─────────────────────────────────────────┐
│ 1. Toast: "조사를 시작했습니다"         │ (status = 'scraping')
├─────────────────────────────────────────┤
│ 2. Status 변경: 'fetching'               │
│    UI: 로딩 스피너 표시                  │
├─────────────────────────────────────────┤
│ 3. 폴링 시작: /api/v1/scrape/results    │
│    - 500ms 대기                         │
│    - 결과 없으면 750ms 대기 (1.5배)    │
│    - 최대 30초까지 계속                 │
├─────────────────────────────────────────┤
│ 4. 데이터 수신!                         │
│    - ScrapeResultsDisplay 표시          │
│    - 임플란트 키워드의 순위 데이터 표시 │
│    - "계속" 버튼 표시                   │
└─────────────────────────────────────────┘
```

**검증 방법**:
- 브라우저 DevTools (F12) → Network 탭
- `/api/v1/scrape/results` 요청 여러 번 보이는지 확인
- 응답이 `"has_data": true`로 바뀌는지 확인

---

### Scenario 2: 에러 핸들링 (Phase 2-1 검증)

**목표**: 잘못된 입력이나 서버 오류 시 상세 에러 메시지 표시

**단계 A - 빈 키워드로 시도**:
1. SetupWizard Step 3에서 키워드를 비우기
2. "조사 시작" 버튼 클릭
3. 유효성 검증 에러 표시 확인

**기대**: Toast 메시지 "키워드를 입력해주세요"

**단계 B - 동시 요청 방지 (다음 Scenario 3에서 테스트)**

---

### Scenario 3: 동시 요청 방지 (Phase 2-3 검증)

**목표**: 같은 키워드로 두 번 스크래핑 시도 시 409 에러

**단계**:
1. Scenario 1처럼 "임플란트" 키워드로 스크래핑 시작
2. 데이터가 오기 전에 (약 5초 내) 다시 "조사 시작" 버튼 클릭
3. 또는 네트워크 탭에서 두 번째 POST 요청 확인

**기대 동작**:
```
두 번째 요청 응답:
HTTP 409 Conflict
{
  "detail": "네이버 플레이스 '임플란트' 조사가 이미 진행 중입니다. 완료될 때까지 기다려주세요."
}

UI: Toast 메시지로 위 메시지 표시
UI: "조사 시작" 버튼 비활성화 (scrapingStatus = 'scraping' 중이므로)
```

**검증 방법**:
- Network 탭에서 두 번째 POST 응답 상태 코드 확인 (409)
- Console에서 에러 메시지 출력 확인

---

## 📊 Network 탭 검증 체크리스트

DevTools → Network 탭에서 다음을 확인하세요:

```
✅ POST /api/v1/scrape/place (또는 view/ad)
   ├─ Status: 200 OK
   └─ Response: { "task_id": "...", "message": "..." }

✅ GET /api/v1/scrape/results (폴링 요청들)
   ├─ 첫 번째 요청: { "has_data": false, "results": [] }
   ├─ 두 번째 요청: { "has_data": false, "results": [] }
   ├─ ...
   └─ 최종 요청: { "has_data": true, "results": [...] }

✅ (중복 시도 시) 두 번째 POST 요청
   ├─ Status: 409 Conflict ⚠️
   └─ Response: { "detail": "이미 진행 중입니다..." }
```

---

## 🔍 만약 데이터가 안 온다면?

### 원인 1: 테스트 데이터 미생성

```bash
# 1. 데이터 생성 API 호출 확인
curl -X POST "https://dentalanal-864421937037.us-west1.run.app/api/v1/status/dev/seed-test-data"

# 2. 응답이 "SUCCESS"인지 "ALREADY_SEEDED"인지 확인
```

### 원인 2: 클라이언트 ID 불일치

SetupWizard에서 사용 중인 `client_id`가 시드 데이터의 클라이언트 ID와 맞는지 확인:

```bash
# 시드된 클라이언트 조회
SELECT * FROM clients WHERE name = 'A 치과';

# SetupWizard에서 사용하는 client_id와 비교
# (LocalStorage에서 client_id 확인)
```

### 원인 3: 키워드가 DB에 없음

```bash
# 시드된 키워드 확인
SELECT * FROM keywords WHERE term = '임플란트';

# 만약 없다면 테스트 데이터가 제대로 생성되지 않은 것
# → 테스트 데이터 생성 API 다시 실행
```

### 원인 4: 결과 조회 엔드포인트 에러

Network 탭에서 `/api/v1/scrape/results` 응답 확인:

```json
{
  "has_data": false,
  "message": "No keyword record found"  // 키워드 없음
}

또는

{
  "has_data": false,
  "message": "No ranking data found yet"  // 순위 데이터 없음
}
```

---

## 📋 최종 검증 체크리스트

모든 항목에 ✅ 표시되었을 때 Phase 2 완료:

- [ ] **배포 완료**: `/health` 엔드포인트 응답 확인
- [ ] **데이터 시드**: `/dev/seed-test-data` API 호출 완료
- [ ] **정상 폴링**: 500ms-3초 간격으로 `/api/v1/scrape/results` 요청 확인
- [ ] **폴링 결과**: 데이터 수신 후 ScrapeResultsDisplay 표시
- [ ] **에러 메시지**: 상세 에러 메시지 UI에 표시됨
- [ ] **동시 요청 방지**: 중복 시도 시 409 Conflict 반환
- [ ] **UI 상태**: Status 변화 (idle → scraping → fetching → done)
- [ ] **버튼 비활성화**: 스크래핑 중 입력 필드 및 버튼 비활성화

---

## 🚀 배포 상태

| 항목 | 상태 | 시간 |
|------|------|------|
| 코드 변경 | ✅ 완료 | 62d376f |
| Git Push | ✅ 완료 | 방금 |
| GitHub Actions | ⏳ 진행 중 | 약 5-10분 |
| Cloud Run 배포 | ⏳ 예정 | 약 10-15분 |
| 테스트 가능 | 🟡 대기 중 | 약 15-20분 |

**현재 시간부터 약 20분 후에 모든 기능을 테스트할 수 있습니다.**

---

## 📞 문제 발생 시

다음 로그를 확인하세요:

```bash
# 프로덕션 로그 (Cloud Run)
https://console.cloud.google.com/run?project=dentalanal

# 또는 명령어로 (gcloud 설치 필요)
gcloud run logs read --limit 50 --platform managed --region us-west1

# 에러 메시지 검색
# - "조사" → 스크래핑 관련 에러
# - "폴링" → polling 관련 에러
# - "409" → 동시 요청 관련
```

---

## 📚 참고 자료

- [Phase 2 완료 보고서](./PHASE2_COMPLETION_REPORT.md)
- [Phase 2 기술 요약](./memory/phase2_summary.md)
- SetupWizard 컴포넌트: `frontend/src/components/setup/SetupWizard.tsx`
- 백엔드 엔드포인트: `backend/app/api/endpoints/scrape.py`
- 테스트 데이터: `backend/app/scripts/debug_seed.py`

---

**다음 단계**: 모든 검증이 완료되면 Phase 3 (고급 분석 기능) 개발 시작

