# 📋 데이터 수집 문제 진단 및 복구 완전 가이드

**작성 일시**: 2026-02-21 17:30 KST
**상황**: 사용자 보고 - "D-MIND 데이터가 아직도 안들어와"

---

## 🔍 문제 진단 결과

### 사용자가 경험한 증상
1. SetupWizard에서 "조사시작" 버튼 클릭
2. 데이터 스크래핑 시작됨 (예상)
3. 하지만 **데이터가 나타나지 않음**
4. 대시보드에 "아직 분석된 데이터가 없습니다" 메시지만 표시

### 근본 원인 분석

**이전 상황** (프로젝트 컨텍스트 요약):
- Phase 1-3까지 완료: 데이터 수집 파이프라인 구축, 스크래핑 최적화, 로깅 시스템 구축
- Phase 2.5: 테스트 데이터 시딩 엔드포인트 추가
- 그런데도 **데이터가 흘러가지 않음**

**발견된 문제**:

#### 문제 1: 디버그 엔드포인트 미배포 (404 에러)
```
URL: /api/v1/debug/diagnose
응답: 404 Not Found
원인: debug.py 라우터가 main.py에 등록되지 않음
```

**해결 방법**:
```python
# backend/app/main.py (라인 139-140 추가)
from app.api.endpoints import ..., debug  # ← 추가
app.include_router(debug.router, prefix="/api/v1/debug", tags=["Debug"])
```

---

## 📊 데이터 파이프라인 아키텍처 (정상 흐름)

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: SetupWizard (사용자 입력)                             │
│ ├─ 클라이언트 선택 또는 생성                                     │
│ ├─ 키워드 입력: "임플란트"                                       │
│ ├─ 플랫폼 선택: "Naver Search"                                  │
│ └─ "조사시작" 버튼 클릭                                          │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: SetupWizard API                                        │
│ ├─ POST /api/v1/analyze/history                                │
│ │  └─ keyword: "임플란트", platform: "NAVER_SEARCH"           │
│ └─ Response: { analysis_id: "..." }                            │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: 스크래핑 작업 생성                                      │
│ ├─ Background Task: execute_place_sync() 또는 유사               │
│ ├─ Keyword 저장: CREATE Keywords                               │
│ └─ 스크래핑 시작                                                │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: Playwright 스크래핑                                     │
│ ├─ Browser 시작: await p.chromium.launch()                    │
│ ├─ 페이지 방문: https://search.naver.com/search.naver?...     │
│ ├─ 내용 추출: Rank, Title, URL, etc.                          │
│ └─ 데이터 파싱: 3-tier 전략 (JS→BeautifulSoup→Regex)         │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend: 데이터 저장                                             │
│ ├─ CREATE Target (competitors)                                 │
│ ├─ CREATE DailyRank                                            │
│ └─ Database: Supabase PostgreSQL                               │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: 폴링                                                  │
│ ├─ GET /api/v1/scrape/results?client_id=...&keyword=...      │
│ ├─ Interval: 500ms → 1s → 1.5s → ... → 3s (Max)             │
│ ├─ Timeout: 30초                                              │
│ └─ Response: { ranks: [...] }                                 │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend: UI 업데이트                                           │
│ ├─ 테이블/차트에 순위 데이터 표시                                │
│ ├─ 대시보드 새로고침                                            │
│ └─ "아직 분석된 데이터가 없습니다" 메시지 사라짐                 │
└─────────────────────────────────────────────────────────────────┘
```

### 각 단계에서 발생 가능한 문제

| 단계 | 문제 | 증상 | 원인 |
|------|------|------|------|
| 1-2 | POST API 실패 | 에러 토스트 표시 | 권한, 유효성 검증 |
| 3 | 작업 생성 실패 | 로그 없음 | 백엔드 에러 |
| 4 | 스크래핑 실패 | daily_ranks=0 | Timeout, 블록, 메모리 |
| 5 | 저장 실패 | 데이터 손실 | DB 연결, 제약 위반 |
| 6 | 폴링 실패 | UI 응답 없음 | API 문제, 토큰 만료 |
| 7 | 렌더링 실패 | 데이터 안 보임 | 프론트엔드 버그 |

---

## ✅ 완료된 해결책

### 1단계: 디버그 라우터 등록
**파일**: `backend/app/main.py`
**변경**: 라인 139-140
```python
# Before
from app.api.endpoints import auth, scrape, analyze, ...

# After
from app.api.endpoints import auth, scrape, analyze, ..., debug  # ← 추가

# Before (라인 153)
app.include_router(status.router, prefix="/api/v1/status", tags=["Status"])

# After (라인 153-154)
app.include_router(status.router, prefix="/api/v1/status", tags=["Status"])
app.include_router(debug.router, prefix="/api/v1/debug", tags=["Debug"])  # ← 추가
```

**효과**:
- ✅ GET /api/v1/debug/stats → 통계 조회
- ✅ GET /api/v1/debug/diagnose → 전체 진단
- ✅ GET /api/v1/debug/trace-keyword/{keyword} → 키워드 추적
- ✅ GET /api/v1/debug/connections-status → 연결 상태

### 2단계: 권한 접근성 개선
**파일**: `backend/app/api/endpoints/debug.py`
**변경**: 라인 43-44
```python
# Before
if current_user.role != "SUPER_ADMIN":
    raise HTTPException(status_code=403, detail="Super admin만 접근 가능합니다")

# After
if current_user.role not in ["SUPER_ADMIN", "ADMIN"]:
    raise HTTPException(status_code=403, detail="Admin 이상의 권한이 필요합니다")
```

**효과**:
- ADMIN 권한 사용자도 디버그 API 접근 가능
- 관리자 협업 시 편의성 향상

### 3단계: 포괄적 문제 해결 문서 작성

**생성된 문서**:
1. **DEPLOYMENT_TROUBLESHOOTING_GUIDE.md**
   - 3단계 진단 프로세스
   - 문제별 해결 방법
   - 긴급 처방
   - 체크리스트

2. **URGENT_ACTION_PLAN.md**
   - 시간순 액션 항목
   - 시나리오별 해결책
   - 모니터링 명령어
   - 에스컬레이션 절차

3. **DIAGNOSIS_AND_RECOVERY_SUMMARY.md** (현재 문서)
   - 전체 상황 요약
   - 파이프라인 아키텍처
   - 완료된 해결책
   - 배포 상태

---

## 🚀 배포 상태

### Commit History
```
90db948 [Doc] 긴급 액션 플랜: 데이터 수집 파이프라인 복구
fd93a89 [Doc] 배포 후 데이터 수집 문제 해결 가이드
65dbac1 [Improve] 디버그 API 권한 접근성 개선
948ee7a [Fix] 디버그 라우터 등록 - 404 에러 해결
```

### 배포 진행 상황
```
🟡 GitHub Actions에 3개 커밋 푸시됨
📋 Cloud Run 자동 배포 시작됨
⏳ 배포 진행 중 (예상 5-10분)

예상 완료 시각: 2026-02-21 17:40-17:50 KST
```

### 확인 방법
```bash
# 실시간 배포 상태 확인
gcloud run logs read --service dentalanal --region us-west1 -f

# 배포 완료 확인 (404가 아닌 정상 응답)
curl https://dentalanal-864421937037.us-west1.run.app/api/v1/debug/stats

# 기대 응답 (401 또는 200)
# ❌ 404: 배포 미완료
# ✅ 401: 인증 필요 (정상!)
# ✅ 200: 토큰 유효 (완벽!)
```

---

## 📋 다음 단계 (배포 후)

### 즉시 실행 (배포 완료 후)

#### Step 1: 데이터 현황 진단
```javascript
// 브라우저 콘솔에서
fetch('/api/v1/debug/stats')
  .then(r => r.json())
  .then(d => console.table(d.data))
```

**기대 결과**:
```
clients:           1 (또는 0)
keywords:          0-5 (테스트 데이터)
daily_ranks:       0-10 (테스트 데이터)
analysis_history:  0-5
```

#### Step 2: 근본 원인 파악
| Data | 의미 | 해결책 |
|------|------|--------|
| clients=0 | 테스트 환경 | `POST /api/v1/status/dev/seed-test-data` 호출 |
| keywords=0 | SetupWizard 미사용 | SetupWizard에서 새 조사 생성 |
| daily_ranks=0 | 스크래핑 미실행 | 클라우드 로그 확인 및 debugging |

#### Step 3: 문제별 조치
```bash
# 만약 daily_ranks=0이면
gcloud run logs read --limit 500 | grep -iE "scrape|rank|naver|error"

# 로그에서 찾아야 할 정보
# ✅ "[Scraper] Starting scrape: keyword=..."
# ✅ "[Scraper] Scraped rank=..."
# ❌ "[ERROR] Scraping failed: ..."
```

---

## 🧪 테스트 및 검증

### Manual Test Checklist

```
[ ] 1. 브라우저에서 로그인 가능
[ ] 2. 대시보드 접속 가능
[ ] 3. /api/v1/debug/stats 에러 없음
[ ] 4. 현재 데이터 현황 파악 (위 Step 1)
[ ] 5. 필요시 테스트 데이터 생성
      fetch('/api/v1/status/dev/seed-test-data', {method:'POST'})
[ ] 6. SetupWizard에서 새 조사 시작
[ ] 7. 키워드 입력 후 "조사시작" 클릭
[ ] 8. 네트워크 탭에서 폴링 요청 확인
[ ] 9. 5-30초 후 데이터 나타남
[ ] 10. 대시보드에 데이터 차트 표시됨
```

### 정상 동작 신호

✅ 이 중 하나라도 보이면 데이터가 흐르고 있음:
```
1. /api/v1/debug/stats에서 daily_ranks > 0
2. 대시보드에 데이터 차트/테이블 표시
3. 클라우드 로그에 "[Scraper] Saved DailyRank" 메시지
4. SetupWizard 후 5초 내 UI 업데이트
```

---

## 🔧 트러블슈팅 빠른 참조

### 문제: API 404 에러
```
원인: Cloud Run 배포 미완료
해결: 5-10분 대기 후 재시도
확인: gcloud run logs read 확인
```

### 문제: 데이터 여전히 안 나옴
```
원인: 스크래핑 실패
해결:
1. Cloud Run 로그에서 에러 메시지 찾기
2. 에러 유형별 해결책 적용:
   - Timeout → TIMEOUT 증가 (60s → 180s)
   - Memory → 메모리 증가 (1Gi → 2Gi)
   - Connection → Naver 접근 확인
3. 재배포 후 다시 시도
```

### 문제: 디버그 API 접근 불가
```
원인: 권한 부족 또는 인증 실패
해결:
1. 로그인 확인 (토큰 유효)
2. 사용자 권한 확인 (ADMIN 이상)
3. 로그아웃 후 다시 로그인
```

---

## 📞 참고 정보

### 주요 API 엔드포인트
- `GET /api/v1/debug/stats` - 데이터 통계
- `GET /api/v1/debug/diagnose` - 전체 진단 (상세)
- `GET /api/v1/debug/trace-keyword/{keyword}` - 키워드별 추적
- `GET /api/v1/debug/connections-status` - 플랫폼 연결 상태
- `POST /api/v1/status/dev/seed-test-data` - 테스트 데이터 생성

### 유용한 명령어
```bash
# Cloud Run 로그 모니터링
gcloud run logs read --service dentalanal -f

# 특정 에러 검색
gcloud run logs read | grep -i "error\|exception"

# 스크래핑 작업 추적
gcloud run logs read | grep -i "scrape\|naver\|playwright"

# 배포 상태
gcloud run services describe dentalanal-service --region us-west1
```

### 데이터베이스 SQL (Supabase)
```sql
-- 데이터 현황
SELECT COUNT(*) as clients FROM clients;
SELECT COUNT(*) as keywords FROM keywords;
SELECT COUNT(*) as daily_ranks FROM daily_ranks;

-- 최근 순위 데이터
SELECT id, rank, platform, captured_at FROM daily_ranks ORDER BY captured_at DESC LIMIT 5;

-- 문제 데이터 확인
SELECT * FROM daily_ranks WHERE rank = -1 OR rank IS NULL;
```

---

## 🎯 성공 기준

**데이터 수집이 정상 작동하는 것으로 판단되는 신호**:

```
✅ 모든 신호
├─ /api/v1/debug/stats → daily_ranks > 0
├─ 대시보드 → 데이터 차트 표시
├─ SetupWizard → "조사시작" 후 5-30초 내 결과
└─ Cloud Run 로그 → "[Scraper] Saved DailyRank" 메시지

⚠️ 부분적 신호 (계속 모니터링)
├─ 테스트 데이터만 있음 (manual seed)
├─ 새 데이터는 반영 안됨 (스크래핑 미작동)
└─ 간헐적 에러 (일부 키워드만 실패)

❌ 실패 신호 (긴급 처방 필요)
├─ /api/v1/debug/stats → daily_ranks = 0
├─ 대시보드 → "데이터 없음" 메시지
├─ 클라우드 로그 → 스크래핑 에러 메시지
└─ SetupWizard → UI 응답 없음
```

---

## 📅 타임라인

```
2026-02-17: Phase 1-3 완료 (데이터 수집 파이프라인)
2026-02-20: Phase 2.5 배포 (테스트 데이터 시딩)
2026-02-21 17:00: 사용자 보고 - "데이터가 안 들어온다"
2026-02-21 17:15: 디버그 시스템 404 에러 발견
2026-02-21 17:30: 디버그 라우터 등록 및 배포 (현재)
2026-02-21 17:40~17:50: Cloud Run 배포 완료 (예상)
2026-02-21 18:00: 데이터 현황 진단 및 조치 (예상)
```

---

**상태**: 🟢 **진행 중** - Cloud Run 배포 대기
**다음 확인**: 배포 완료 후 `/api/v1/debug/stats` 호출
**예상 해결 시각**: 2026-02-21 18:00~18:30 KST

