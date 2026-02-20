# 🔍 데이터 디버깅 가이드

**작성일**: 2026-02-21  
**목적**: SetupWizard 데이터 흐름 전체 추적 및 문제 해결

---

## 📊 데이터 흐름 전체 구조

```
Frontend (SetupWizard)
    ↓
사용자 입력 (키워드, 플랫폼)
    ↓
POST /api/v1/scrape/create (analysis_history 생성)
    ↓
Backend 스크래핑 작업
    ├─ GET Naver Maps 페이지
    ├─ JavaScript 렌더링
    ├─ HTML 파싱
    └─ 데이터 추출
    ↓
데이터 정규화
    ├─ Keywords 테이블 저장
    ├─ Targets 테이블 저장
    └─ DailyRanks 테이블 저장
    ↓
Frontend 폴링 (결과 조회)
    └─ GET /api/v1/scrape/results
    ↓
대시보드 표시
    ├─ CompetitorComparison
    ├─ KeywordRankTable
    └─ RankingChart
```

---

## 🔧 디버깅 도구

### 1. 전체 진단 실행

```bash
# 모든 데이터베이스 상태 확인
GET /api/v1/debug/diagnose

# 응답 예시:
{
  "status": "success",
  "data": {
    "timestamp": "2026-02-21T10:30:00",
    "sections": {
      "tables": {
        "clients": true,
        "keywords": true,
        "daily_ranks": true,
        ...
      },
      "clients": {
        "count": 1,
        "details": [
          {
            "name": "A 치과",
            "keywords": 3,
            "daily_ranks": 15
          }
        ]
      },
      "daily_ranks": {
        "count": 15,
        "platforms": {
          "NAVER_PLACE": 15
        }
      }
    },
    "issues": [],
    "recommendations": []
  }
}
```

### 2. 빠른 통계 조회

```bash
# 데이터 개수 즉시 확인
GET /api/v1/debug/stats

# 응답:
{
  "status": "success",
  "data": {
    "clients": 1,
    "keywords": 3,
    "daily_ranks": 15,
    "analysis_history": 5
  }
}
```

### 3. 키워드 흐름 추적

```bash
# 특정 키워드의 전체 흐름 추적
GET /api/v1/debug/trace-keyword/임플란트?client_id=abc123

# 응답:
{
  "status": "success",
  "data": {
    "keyword": "임플란트",
    "client_id": "abc123",
    "daily_ranks_count": 5,
    "analysis_history_count": 2,
    "recent_ranks": [
      {
        "rank": 3,
        "platform": "NAVER_PLACE",
        "captured_at": "2026-02-21T10:15:00"
      }
    ],
    "recent_analysis": [
      {
        "is_saved": false,
        "created_at": "2026-02-21T10:20:00"
      }
    ]
  }
}
```

### 4. 연결 상태 확인

```bash
# 플랫폼 연결 상태 확인
GET /api/v1/debug/connections-status

# 응답:
{
  "status": "success",
  "data": {
    "connections": {
      "NAVER_PLACE": {
        "total": 1,
        "active": 1,
        "inactive": 0
      },
      "NAVER_AD": {
        "total": 1,
        "active": 1,
        "inactive": 0
      }
    },
    "total_connections": 2
  }
}
```

---

## 🔴 데이터가 없을 때 체크리스트

### Step 1: 클라이언트 확인
```python
# 데이터베이스에서 직접 확인
SELECT * FROM clients;

# 비어있으면:
# → POST /dev/seed-test-data로 테스트 데이터 생성
# → 또는 SetupWizard에서 새 클라이언트 생성
```

### Step 2: 키워드 저장 확인
```python
SELECT * FROM keywords;

# 비어있으면:
# → SetupWizard 입력 폼 확인
# → POST /api/v1/analysis/create 엔드포인트 테스트
```

### Step 3: 스크래핑 실행 확인
```python
# Cloud Run 로그 확인
gcloud run logs read --service=dentalanal

# 에러가 있으면:
# → AdvancedNaverPlaceScraper 테스트
# → python test_naver_advanced.py
```

### Step 4: DailyRanks 저장 확인
```python
SELECT COUNT(*) FROM daily_ranks;

# 0이면:
# → 스크래핑 파이프라인 검증
# → /api/v1/scrape/results 응답 확인
```

### Step 5: API 응답 확인
```bash
# SetupWizard에서 응답 받는지 확인
# 브라우저 개발자 도구 → Network 탭

# GET /api/v1/scrape/results?client_id=...&keyword=...&platform=...
# 응답 페이로드 확인
```

---

## 💡 일반적인 문제와 해결책

### 문제 1: DailyRanks가 비어있음

**진단**:
```bash
GET /api/v1/debug/stats
# daily_ranks: 0
```

**원인**:
1. 스크래핑이 실패함
2. 데이터가 저장되지 않음
3. Naver API가 응답하지 않음

**해결책**:
```python
# 1. Cloud Run 로그 확인
gcloud run logs read --limit 100

# 2. 스크래핑 로그 확인
SELECT * FROM raw_scraping_logs;

# 3. AdvancedNaverPlaceScraper 직접 테스트
python test_naver_advanced.py --keyword "임플란트"

# 4. HTML wrapper 문제 확인
# → base.py의 regex 패턴 검증

# 5. Naver가 차단했는지 확인
# → headless=False로 실행하여 화면 확인
```

### 문제 2: Keywords는 있는데 DailyRanks가 없음

**진단**:
```bash
GET /api/v1/debug/trace-keyword/임플란트
# daily_ranks_count: 0
```

**원인**:
1. 스크래핑 작업이 실행되지 않음
2. 스크래핑은 되었지만 저장되지 않음

**해결책**:
```python
# 1. AnalysisHistory 확인
SELECT * FROM analysis_history WHERE keyword = '임플란트';

# 2. 결과 저장 로직 확인
# → scrape_place_task 함수 검증
# → 데이터 정규화 로직 검증

# 3. 수동으로 DailyRank 생성 테스트
from app.models.models import Keyword, Target, DailyRank
from app.core.database import SessionLocal

db = SessionLocal()
kw = db.query(Keyword).filter_by(term="임플란트").first()
target = db.query(Target).first()

dr = DailyRank(
    keyword_id=kw.id,
    target_id=target.id,
    platform="NAVER_PLACE",
    rank=3,
    client_id=kw.client_id
)
db.add(dr)
db.commit()
```

### 문제 3: SetupWizard에서 결과가 표시되지 않음

**진단**:
```bash
# 1. DailyRanks가 있는지 확인
GET /api/v1/debug/stats

# 2. API 응답이 올바른지 확인
GET /api/v1/scrape/results?client_id=...&keyword=...&platform=...
```

**원인**:
1. 폴링 타임아웃
2. API 응답 지연
3. Frontend 필터링 오류

**해결책**:
```python
# 1. /scrape/results 엔드포인트 성능 확인
# → 쿼리 최적화 (N+1 문제 해결)
# → 인덱스 추가

# 2. Frontend 폴링 로직 확인
# → SetupWizard.tsx의 getScrapeResults()
# → 타임아웃 증가 (30초 → 60초)

# 3. 콘솔 에러 확인
# → 브라우저 개발자 도구 F12
# → Console 탭에서 에러 메시지 확인
```

---

## 📈 성능 모니터링

### Database 쿼리 성능
```python
# 느린 쿼리 식별
import time

start = time.time()
results = db.query(DailyRank).filter(
    DailyRank.client_id == client_id
).all()
elapsed = time.time() - start

print(f"Query time: {elapsed:.3f}s")
# 1초 이상이면 인덱스 추가 필요
```

### API 응답 시간
```bash
# curl로 응답 시간 측정
curl -w "Time: %{time_total}s\n" \
  https://api.dentalanal.com/api/v1/scrape/results?...
```

### Cloud Run 메트릭
```bash
# CPU, 메모리 사용량 확인
gcloud monitoring read \
  --filter='resource.service.name = "dentalanal"' \
  --format=json
```

---

## 🛠️ 실시간 디버깅 명령어

### 테스트 데이터 생성
```bash
curl -X POST http://localhost:8000/api/v1/status/dev/seed-test-data
```

### 특정 클라이언트의 모든 데이터 조회
```bash
# Cloud SQL에서
SELECT 
  c.name as client,
  COUNT(k.id) as keywords,
  COUNT(dr.id) as daily_ranks,
  COUNT(ah.id) as analysis
FROM clients c
LEFT JOIN keywords k ON c.id = k.client_id
LEFT JOIN daily_ranks dr ON c.id = dr.client_id
LEFT JOIN analysis_history ah ON c.id = ah.client_id
GROUP BY c.id;
```

### 최근 스크래핑 결과
```bash
# 지난 1시간
SELECT 
  keyword,
  platform,
  COUNT(*) as count,
  MAX(captured_at) as latest
FROM raw_scraping_logs
WHERE captured_at > NOW() - INTERVAL '1 hour'
GROUP BY keyword, platform
ORDER BY latest DESC;
```

---

## 📝 로그 분석

### Cloud Run 로그 필터링
```bash
# 스크래핑 오류만
gcloud run logs read --filter='severity=ERROR AND message="[Scrape"'

# 특정 키워드
gcloud run logs read --filter='message~"임플란트"'

# 과거 1시간
gcloud run logs read --limit 1000 --filter='timestamp>="2026-02-21T09:00:00Z"'
```

### 로컬 로그 확인
```python
# FastAPI 서버 시작할 때
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# 그러면 모든 DEBUG 로그가 출력됨
```

---

## 🎯 권장 모니터링 설정

### 1. 실시간 경고
```python
# 만약 DailyRanks가 24시간 이상 없으면 알림
SELECT COUNT(*) FROM daily_ranks 
WHERE captured_at > NOW() - INTERVAL '24 hours';
```

### 2. 스크래핑 실패율 모니터링
```python
# 실패율 = (실패 / 총 요청) * 100
SELECT 
  (SELECT COUNT(*) FROM analysis_history WHERE result_data IS NULL) * 100.0 /
  (SELECT COUNT(*) FROM analysis_history) as failure_rate;
```

### 3. API 응답 시간 모니터링
```python
# 슬로우 쿼리 감지
SELECT 
  query,
  COUNT(*) as executions,
  AVG(duration) as avg_duration,
  MAX(duration) as max_duration
FROM query_logs
GROUP BY query
HAVING AVG(duration) > 1000  # 1초 이상
ORDER BY max_duration DESC;
```

---

## 📞 문제 해결 체크리스트

- [ ] 클라이언트 데이터 확인
- [ ] 키워드 저장 확인
- [ ] 스크래핑 작업 실행 확인
- [ ] DailyRanks 저장 확인
- [ ] API 응답 확인
- [ ] Frontend 폴링 확인
- [ ] 대시보드 표시 확인
- [ ] Cloud Run 로그 검토
- [ ] 데이터베이스 연결 확인
- [ ] 권한 확인

---

## 🚀 다음 단계

1. **진단 API 배포** (오늘)
   - GET /api/v1/debug/diagnose
   - GET /api/v1/debug/stats
   - GET /api/v1/debug/trace-keyword/{keyword}

2. **실시간 모니터링** (내일)
   - Cloud Monitoring 대시보드 설정
   - 실패 경고 설정
   - 성능 메트릭 추적

3. **자동 복구** (이번 주)
   - 스크래핑 실패 시 자동 재시도
   - 타임아웃 조정
   - 캐싱 추가

---

**최종 목표**: SetupWizard에서 "조사시작" 클릭 후 5초 내에 데이터 표시 ✅
