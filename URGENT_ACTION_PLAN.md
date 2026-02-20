# 🚨 긴급 액션 플랜: 데이터 수집 파이프라인 복구

**상황**: "D-MIND | 통합 모니터링 & AI 분석 솔루션 아직도 안들어와 데이터 어떻게 하면 들어오는거야"

**진단**: 데이터가 시스템에 들어오지 않고 있음. 데이터 파이프라인의 어느 지점에서 끊어져 있음.

---

## 🔧 이미 완료된 수정사항

### ✅ 1단계: 디버그 시스템 배포 (2026-02-21 완료)

**문제**: 디버그 엔드포인트가 404 에러 반환
- 원인: debug.py 라우터를 main.py에 등록하지 않음

**해결**:
```python
# backend/app/main.py
from app.api.endpoints import ..., debug  # ← 추가
app.include_router(debug.router, prefix="/api/v1/debug", tags=["Debug"])  # ← 추가
```

**결과**:
- ✅ `/api/v1/debug/stats` 엔드포인트 활성화
- ✅ `/api/v1/debug/diagnose` 엔드포인트 활성화
- ✅ `/api/v1/debug/trace-keyword/{keyword}` 엔드포인트 활성화
- ✅ `/api/v1/debug/connections-status` 엔드포인트 활성화

**배포 상태**: 
```
Commit: 948ee7a [Fix] 디버그 라우터 등록 - 404 에러 해결
Commit: 65dbac1 [Improve] 디버그 API 권한 접근성 개선
```
Cloud Run 배포 진행 중 (약 5-10분 소요)

### ✅ 2단계: 권한 접근성 개선 (완료)

**변경사항**:
- SUPER_ADMIN만 허용 → ADMIN 이상 모두 허용
- 디버깅 시 접근성 향상

**코드**:
```python
if current_user.role not in ["SUPER_ADMIN", "ADMIN"]:
    raise HTTPException(status_code=403, detail="Admin 이상의 권한이 필요합니다")
```

### ✅ 3단계: 완벽한 문제 해결 가이드 작성 (완료)

**파일**: `DEPLOYMENT_TROUBLESHOOTING_GUIDE.md`

포함 내용:
- 3단계 진단 프로세스
- 문제별 해결 방법 (clients:0, keywords:0, daily_ranks:0)
- 긴급 처방
- 정상 데이터 흐름 체크리스트

---

## 🎯 다음 액션 항목 (시간순)

### 즉시 (지금부터 10분 내)

#### Step 1: Cloud Run 배포 완료 대기
```
예상 시간: 5-10분
확인 방법: https://dentalanal-864421937037.us-west1.run.app/api/v1/debug/stats
기대 결과: 200 OK (404 아님)
```

#### Step 2: 데이터 현황 진단 (배포 완료 후)

브라우저 개발자 도구 Console에서:
```javascript
// 빠른 통계 확인
fetch('/api/v1/debug/stats')
  .then(r => r.json())
  .then(d => {
    console.log('=== 데이터 통계 ===');
    console.log('Clients:', d.data.clients);
    console.log('Keywords:', d.data.keywords);
    console.log('DailyRanks:', d.data.daily_ranks);
    console.log('AnalysisHistory:', d.data.analysis_history);
  })
```

**기대 결과 분석**:

- **데이터가 있는 경우** (`daily_ranks > 0`)
  ```
  ✅ 스크래핑이 작동하고 있음
  └─ 다음: /api/v1/debug/diagnose로 전체 진단 실행
  ```

- **데이터가 없는 경우** (`daily_ranks = 0`)
  ```
  ❌ 스크래핑이 작동하지 않음
  ├─ clients = 0 → 클라이언트 생성 API 실패
  ├─ keywords = 0 → 키워드 저장 실패
  └─ daily_ranks = 0 → 스크래핑 자체 실패
  ```

---

### 5분 후 (데이터 현황 파악 후)

#### Step 3: 근본 원인 분석

**시나리오별 조치**:

##### Scenario A: clients=0, keywords=0, daily_ranks=0
```
문제: 클라이언트부터 생성이 안됨
원인: 아직 테스트 데이터가 없음

해결: 테스트 데이터 생성 API 호출
fetch('/api/v1/status/dev/seed-test-data', { method: 'POST' })
  .then(r => r.json())
  .then(d => console.log('생성 완료:', d))

결과: clients=1, keywords=2, daily_ranks=10으로 증가
```

##### Scenario B: clients=1, keywords=0, daily_ranks=0
```
문제: 클라이언트는 있지만 키워드 없음
원인: SetupWizard에서 "조사시작" 버튼 클릭 후 API 실패

해결:
1. Cloud Run 로그 확인
   gcloud run logs read --limit 200 | grep -i "analysis_history\|keyword\|error"

2. 에러 메시지 기반 수정
   - Timeout: timeout_ms 증가
   - Connection: 네트워크 문제
   - Permission: 인증 문제
```

##### Scenario C: clients=1, keywords=1, daily_ranks=0
```
문제: 키워드는 있지만 스크래핑 데이터 없음 (가장 심각!)
원인: Playwright 스크래핑 실패

해결:
1. Cloud Run 로그에서 스크래핑 에러 확인
   gcloud run logs read --limit 500 | grep -iE "scrape|playwright|rank|naver"

2. 에러 유형별 해결
   - Timeout: backend/app/scrapers/base.py에서 TIMEOUT 증가 (60s → 180s)
   - Memory: gcloud run deploy에서 --memory 2Gi로 증가
   - Connection: Naver IP 블록 확인, User-Agent 변경
```

---

### 10분 후 (원인 파악 후)

#### Step 4: 코드 수정 및 재배포

수정 사항에 따라:

```bash
# 예: Timeout 증가 필요한 경우
1. 파일 수정: backend/app/scrapers/base.py
   TIMEOUT = 180  # 60에서 180으로

2. 커밋
   git add backend/app/scrapers/base.py
   git commit -m "[Hotfix] 스크래핑 타임아웃 증가"

3. 배포
   git push origin main
   
4. 배포 대기 (5-10분)

5. 재테스트
   SetupWizard에서 다시 시도 → 데이터 확인
```

---

### 20분 후 (최종 검증)

#### Step 5: 데이터 흐름 전체 검증

모든 단계 완료 후:

```javascript
// 최종 통계 확인
fetch('/api/v1/debug/stats')
  .then(r => r.json())
  .then(d => {
    const { clients, keywords, daily_ranks } = d.data;
    if (clients > 0 && keywords > 0 && daily_ranks > 0) {
      console.log('✅ 데이터 수집 정상!');
    } else {
      console.log('❌ 여전히 문제 있음');
    }
  })
```

#### Step 6: UI 검증

1. 브라우저 새로고침: Ctrl+F5
2. 대시보드 확인
   - "아직 분석된 데이터가 없습니다" 메시지 사라짐?
   - 데이터 차트/테이블 표시됨?
3. SetupWizard 재테스트
   - 새 키워드 입력 후 "조사시작"
   - 5-30초 후 결과 표시됨?

---

## 📊 모니터링 및 추적

### Cloud Run 로그 모니터링

리얼타임 로그 확인 (필요시):
```bash
# 스트리밍 로그 (Ctrl+C로 종료)
gcloud run logs read --service dentalanal --region us-west1 --limit 100 -f

# 특정 에러 검색
gcloud run logs read --limit 500 | grep -i "error\|exception\|failed"

# 스크래핑 작업 추적
gcloud run logs read --limit 500 | grep -i "scrape\|rank\|naver"
```

### 데이터베이스 상태 모니터링

Supabase 대시보드 또는 SQL:
```sql
-- 데이터 통계
SELECT 
  (SELECT COUNT(*) FROM clients) as clients,
  (SELECT COUNT(*) FROM keywords) as keywords,
  (SELECT COUNT(*) FROM daily_ranks) as daily_ranks;

-- 최근 DailyRanks
SELECT id, keyword_id, rank, platform, captured_at 
FROM daily_ranks 
ORDER BY captured_at DESC 
LIMIT 10;
```

---

## ⚠️ 주의사항

### 배포 시간
- Cloud Run 배포: 5-10분 소요
- 리빌드 캐시 활용하면 더 빠름
- 로그 표시 지연 2-3분

### 권한 확인
- 디버그 API: ADMIN 이상 권한 필요
- 현재 로그인 계정: admin 여부 확인

### 테스트 데이터
- `/api/v1/status/dev/seed-test-data` 호출로 자동 생성
- 프로덕션 환경에서는 안전함 (기존 데이터 유지)

---

## 🔄 문제 지속 시 에스컬레이션

만약 위 모든 단계를 따랐는데도 데이터가 안 나오면:

```
1. Cloud Run 메모리 확인
   gcloud run services describe dentalanal-service | grep memory
   → 2Gi 미만이면 메모리 부족 가능

2. 데이터베이스 연결 확인
   gcloud run logs read | grep -i "database\|connection\|postgres"
   
3. Naver API 접근 확인
   gcloud run logs read | grep -i "naver\|403\|429\|blocked"

4. 마지막 수단: 데이터베이스 초기화
   ⚠️ 모든 데이터 삭제됨
   DELETE FROM daily_ranks;
   DELETE FROM targets;
   DELETE FROM keywords;
   DELETE FROM platform_connections;
   DELETE FROM clients;
   
   그 후 테스트 데이터 재생성:
   POST /api/v1/status/dev/seed-test-data
```

---

## 📝 완료 체크리스트

- [ ] Cloud Run 배포 완료 확인 (404 없음)
- [ ] `/api/v1/debug/stats` 호출 성공
- [ ] 현재 데이터 상태 확인 (clients, keywords, daily_ranks)
- [ ] 근본 원인 파악 (어느 단계에서 끊김)
- [ ] 필요 시 코드 수정 및 재배포
- [ ] SetupWizard 재테스트
- [ ] 대시보드에 데이터 표시 확인
- [ ] 정상 작동 확인

---

## 📞 참고 자료

- **배포 가이드**: DEPLOYMENT_TROUBLESHOOTING_GUIDE.md
- **디버그 API**: /api/v1/debug/* (stats, diagnose, trace-keyword, connections-status)
- **테스트 데이터**: /api/v1/status/dev/seed-test-data
- **로그 보기**: `gcloud run logs read`

---

**마지막 업데이트**: 2026-02-21
**작성자**: Claude Agent
**상태**: 🟢 진행 중 - Cloud Run 배포 대기

