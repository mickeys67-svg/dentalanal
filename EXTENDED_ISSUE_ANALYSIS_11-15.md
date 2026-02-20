# 🔴 DentalAnal 시스템 - 추가 5가지 문제점 분석 (11-15)

> **고급 기술 이슈 분석**
>
> 작성일: 2026-02-20
> 범위: 문제점 11-15 (심화 분석)

---

## 🔴 문제점 11: rank_change 필드 미구현 (데이터 무결성)

### 위치
- **파일**: `backend/app/models/models.py` (라인 243)
- **파일**: `frontend/src/components/setup/ScrapeResultsDisplay.tsx` (라인 14)

### 현재 코드
```python
# backend/app/models/models.py
class DailyRank(Base):
    __tablename__ = "daily_ranks"
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    rank = Column(Integer, nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    # ❌ rank_change 필드가 없음!
```

```typescript
// frontend/src/components/setup/ScrapeResultsDisplay.tsx (라인 8-10)
interface ScrapeResult {
    rank: number;
    rank_change?: number;  // ← API에서 반환되지 않음!
    target_name: string;
    ...
}
```

```python
# backend/app/api/endpoints/analyze.py (라인 933-936)
result_item = {
    "rank": r.rank,
    "rank_change": r.rank_change,  # ← AttributeError: 'DailyRank' has no attribute 'rank_change'
    ...
}
```

### 문제점
```
실제 흐름:
1️⃣ getScrapeResults() 호출
   └─ backend: GET /api/v1/analyze/scrape-results/{client_id}
2️⃣ backend에서 DailyRank 객체 조회
3️⃣ response 구성:
   result_item = {
       "rank": r.rank,
       "rank_change": r.rank_change,  # ❌ AttributeError!
       ...
   }
4️⃣ 500 Internal Server Error 반환
5️⃣ 프론트엔드에서 예외 발생

결과:
  "조사 결과가 없습니다" (실제는 백엔드 에러)
```

### 즉시 현상
```
요청: GET /api/v1/analyze/scrape-results/uuid
응답: 500 Internal Server Error
{
  "detail": "'DailyRank' object has no attribute 'rank_change'"
}

콘솔: 
AttributeError: 'DailyRank' object has no attribute 'rank_change'
File "backend/app/api/endpoints/analyze.py", line 936, in get_scrape_results
    "rank_change": r.rank_change,
```

### 해결 방법
```python
# 방법 1: 모델에 필드 추가
class DailyRank(Base):
    rank = Column(Integer, nullable=False)
    rank_change = Column(Integer, nullable=True, default=0)
    captured_at = Column(DateTime(timezone=True), ...)

# 방법 2: API에서 필드 제거
result_item = {
    "rank": r.rank,
    # "rank_change": r.rank_change,  # 제거
    "target_name": ...
}

# 방법 3: rank_change 계산 로직 추가
# 이전 rank와 현재 rank의 차이 계산
previous_rank = db.query(DailyRank).filter(
    DailyRank.target_id == r.target_id,
    DailyRank.keyword_id == r.keyword_id,
    DailyRank.captured_at < r.captured_at
).order_by(DailyRank.captured_at.desc()).first()

rank_change = (previous_rank.rank - r.rank) if previous_rank else 0
```

**권장**: 방법 1 (모델에 필드 추가) - 가장 확장성 좋음

---

## 🔴 문제점 12: 데이터베이스 세션 누수 (리소스 누수)

### 위치
- **파일**: `backend/app/worker/tasks.py` (라인 33-127)

### 현재 코드
```python
def execute_place_sync(keyword: str, client_id_str: str = None):
    db = SessionLocal()  # ← 세션 생성
    try:
        service = AnalysisService(db)
        if results:
            service.save_place_results(keyword, results, client_uuid)
        
        admins = db.query(User).filter(...).all()
        for admin in admins:
            note = Notification(...)
            db.add(note)
        db.commit()  # ← DB 커밋
        
    except Exception as e:
        logger.error(f"Saving failed: {e}")
        # ❌ db.rollback() 없음!
    finally:
        db.close()  # ← 세션 닫기
    
    return results
```

### 문제점

```
시나리오: 데이터 저장 중 예외 발생

1️⃣ service.save_place_results() 호출
2️⃣ db.add() 및 db.commit()
3️⃣ ❌ db.flush() 중 에러 발생 (FK 제약조건, 트리거 등)
4️⃣ except 블록으로 이동
   └─ logger.error() 로그만 함
   └─ ❌ db.rollback() 없음!
5️⃣ finally 블록 실행
   └─ db.close()

결과:
  - 부분적으로 저장된 데이터 남음 (일관성 깨짐)
  - 세션은 닫혔지만 트랜잭션 미롤백
  - 다음 세션에서 장애 발생 가능
  - 데이터베이스 락(lock) 발생 가능
```

### 더 심각한 문제

```python
# Notification 저장 시 에러 발생 예시
for admin in admins:  # ← admins 쿼리 성공
    note = Notification(
        user_id=admin.id,  # ← admin이 삭제되었다면?
        ...
    )
    db.add(note)

db.commit()  # ❌ FK 제약조건 위반
# → except 블록으로 이동
# → db.rollback() 없음
# → 이전의 save_place_results()에서 추가한 DailyRank는 남음!
# → 데이터 불일치!
```

### 해결 방법
```python
def execute_place_sync(keyword: str, client_id_str: str = None):
    db = SessionLocal()
    try:
        service = AnalysisService(db)
        if results:
            service.save_place_results(keyword, results, client_uuid)
        
        # ... Notification 추가 ...
        
        db.commit()
    except Exception as e:
        db.rollback()  # ✅ 트랜잭션 롤백
        logger.error(f"Failed: {e}")
    finally:
        db.close()
```

---

## 🟡 문제점 13: 프론트엔드 toast 메시지 일관성 부족

### 위치
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 219-270)

### 현재 코드
```typescript
// Step 1: 분석 이력 저장
const historyResponse = await saveAnalysisHistory({
    client_id: newClientId!,
    keyword,
    platform
});
console.log('✅ Analysis history saved:', historyResponse);

// Step 2: 스크래핑 트리거
toast.info('조사를 시작했습니다. 결과를 수집 중입니다...');

if (platform === 'NAVER_PLACE') {
    scrapePlace(keyword, newClientId!)
        .then(() => {
            console.log('✅ Place scraping triggered');
        })
        .catch((err) => {
            console.error('⚠️ Place scraping failed:', err);
            // ❌ 에러가 발생했는데도 "결과를 수집 중"이라고 표시됨!
        });
}

// Step 3: 2초 대기
setTimeout(async () => {
    const results = await getScrapeResults(newClientId!, keyword, platform);
    
    if (results.has_data && results.results.length > 0) {
        setScrapeResults(results);
        setShowResults(true);
        toast.success('조사가 완료되었습니다!');  // ← 항상 성공으로 표시
    } else {
        setScrapeResults(results);
        setShowResults(true);
        // ❌ 아무 토스트도 표시 안 함 (사용자는 상태를 모름)
        toast.info('조사가 시작되었습니다. 데이터는 잠시 후 나타날 예정입니다.');
    }
}, 2000);
```

### 문제점

```
사용자 경험:

✅ "조사를 시작했습니다"
⏳ 2초 대기
📊 결과 표시
✅ "조사가 완료되었습니다!" (데이터 없어도)

또는

✅ "조사를 시작했습니다"
⏳ 2초 대기
❌ 에러: "Failed to fetch scrape results"
😕 사용자: "뭐가 문제야?"
```

### 미스매칭 메시지

```
실제 상황 vs 메시지:

1. 스크래핑 중 에러
   메시지: "조사를 시작했습니다. 결과를 수집 중입니다..."
   현실: ❌ 스크래핑이 실패함

2. 결과 조회 실패
   메시지: "조사가 시작되었습니다. 데이터는 잠시 후 나타날 예정입니다."
   현실: ❌ 결과를 조회할 수 없음 (API 에러)

3. 네트워크 지연
   메시지: "조사가 완료되었습니다!"
   현실: ⏳ 아직 스크래핑 중
```

### 해결 방법
```typescript
// 상태 플래그 추가
const [scrapingError, setScrapingError] = useState<string | null>(null);
const [scrapingStatus, setScrapingStatus] = useState<'idle' | 'scraping' | 'fetching' | 'done' | 'error'>('idle');

// 에러 플래그 업데이트
.catch((err) => {
    setScrapingError(err.message);
    setScrapingStatus('error');
    toast.error(`스크래핑 실패: ${err.message}`);
});

// 결과 조회 전 상태 업데이트
setScrapingStatus('fetching');

// 결과에 따른 메시지
if (results.has_data && results.results.length > 0) {
    setScrapingStatus('done');
    toast.success('조사가 완료되었습니다!');
} else {
    setScrapingStatus('idle');  // 재시도 가능
    toast.warning('데이터가 아직 준비되지 않았습니다. 잠시 후 다시 시도해주세요.');
}
```

---

## 🟡 문제점 14: 동시 스크래핑 요청 처리 미흡

### 위치
- **파일**: `backend/app/api/endpoints/scrape.py` (라인 11-54)
- **파일**: `frontend/src/components/setup/SetupWizard.tsx` (라인 230-260)

### 현재 코드
```python
# backend/app/api/endpoints/scrape.py
@router.post("/place")
def trigger_place_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    task_id = str(uuid.uuid4())
    # ❌ 같은 keyword + client_id로 이미 진행 중인지 확인 안 함!
    background_tasks.add_task(scrape_place_task, request.keyword, request.client_id)
    
    return ScrapeResponse(task_id=task_id, message="...")
```

```typescript
// frontend/src/components/setup/SetupWizard.tsx
// ❌ 사용자가 버튼을 연타하면?
scrapePlace(keyword, newClientId!)
scrapePlace(keyword, newClientId!)
scrapePlace(keyword, newClientId!)
// 3개의 동일한 작업이 동시에 실행됨!
```

### 문제 시나리오

```
사용자가 "조사 시작" 버튼을 3번 빠르게 클릭:

0ms: scrapePlace() 호출 #1
5ms: scrapePlace() 호출 #2
10ms: scrapePlace() 호출 #3

백그라운드에서:
Task #1: 스크래핑 시작 → DB에 저장
Task #2: 동일한 스크래핑 시작 → 동일한 데이터 다시 저장
Task #3: 또 다시... (중복 데이터 3배!)

결과:
- 네트워크 대역폭 3배 사용
- CPU 3배 사용
- 데이터베이스에 중복 레코드 3개 저장
- 비용 증가
- Naver IP 차단 위험
```

### 데이터베이스 중복 문제

```sql
-- 스크래핑 완료 후
SELECT * FROM daily_ranks 
WHERE client_id = 'UUID' 
AND keyword_id = 'UUID'
AND platform = 'NAVER_PLACE';

결과:
┌─────────────────────────────────────┐
│ id       │ target_id │ rank │ date  │
├──────────┼───────────┼──────┼───────┤
│ uuid-1   │ target-1  │ 1    │ 2/20  │ ← 첫 번째 스크래핑
│ uuid-2   │ target-1  │ 1    │ 2/20  │ ← 중복! (두 번째)
│ uuid-3   │ target-1  │ 1    │ 2/20  │ ← 중복! (세 번째)
└─────────────────────────────────────┘

데이터 분석에서:
SELECT AVG(rank) FROM daily_ranks ...
→ 정확하지 않은 통계 (중복으로 인해)
```

### 해결 방법

```python
# Backend: 진행 중인 작업 추적 테이블 추가
class ScrapeTask(Base):
    __tablename__ = "scrape_tasks"
    id = Column(GUID, primary_key=True)
    client_id = Column(GUID, ...)
    keyword = Column(String, ...)
    platform = Column(String, ...)
    status = Column(String)  # 'PENDING', 'RUNNING', 'DONE', 'FAILED'
    created_at = Column(DateTime, ...)
    completed_at = Column(DateTime, ...)

# Endpoint에서 확인
@router.post("/place")
def trigger_place_scrape(request: ScrapeRequest, db: Session, ...):
    # 진행 중인 작업 확인
    existing = db.query(ScrapeTask).filter(
        ScrapeTask.client_id == request.client_id,
        ScrapeTask.keyword == request.keyword,
        ScrapeTask.status.in_(['PENDING', 'RUNNING'])
    ).first()
    
    if existing:
        return {"status": "ALREADY_RUNNING", "task_id": str(existing.id)}
    
    # 새 작업 생성 및 등록
    task = ScrapeTask(...)
    db.add(task)
    db.commit()
    
    background_tasks.add_task(scrape_place_task, ...)
    return {"status": "SUCCESS", "task_id": str(task.id)}
```

```typescript
// Frontend: 버튼 비활성화
const [isScrapingInProgress, setIsScrapingInProgress] = useState(false);

const handleScrape = async () => {
    if (isScrapingInProgress) {
        toast.warning('이미 조사가 진행 중입니다.');
        return;  // ✅ 중복 요청 방지
    }
    
    setIsScrapingInProgress(true);
    try {
        await scrapePlace(keyword, newClientId!);
    } finally {
        setIsScrapingInProgress(false);
    }
};

// HTML
<button disabled={isScrapingInProgress} onClick={handleScrape}>
    조사 시작
</button>
```

---

## 🟠 문제점 15: ScrapeResultsDisplay 컴포넌트의 제한사항

### 위치
- **파일**: `frontend/src/components/setup/ScrapeResultsDisplay.tsx` (라인 1-121)

### 현재 코드
```typescript
export function ScrapeResultsDisplay({
    scrapeResults,
    onContinue,
    onRetry,
    isLoading = false
}: ScrapeResultsDisplayProps) {
    // ...
    
    {scrapeResults.results.slice(0, 5).map((result, idx) => (
        // ❌ 최대 5개만 표시!
    ))}
    
    {scrapeResults.total_count > 5 && (
        <p className="text-xs text-gray-600 mt-4">
            ... 외 {scrapeResults.total_count - 5}개 결과 (대시보드에서 전체 확인 가능)
        </p>
    )}
}
```

### 문제점 1: 데이터 표시 제한

```
장점: 초기 로딩 빠름
단점: 
  ❌ 사용자가 결과를 충분히 검토할 수 없음
  ❌ 상위 5개 가정이 항상 맞지 않음
  ❌ 하위 데이터를 대시보드에서 찾기 어려움

예시:
keyword: "임플란트" (상위 20개 결과)
표시: 1-5위 (5개)
숨김: 6-20위 (15개)

사용자: "우리 병원이 10위인데 왜 안 보여?"
```

### 문제점 2: platform 문자열 하드코딩

```typescript
{
    scrapeResults.platform === 'NAVER_PLACE' ? '네이버 플레이스' :
    scrapeResults.platform === 'NAVER_VIEW' ? '네이버 VIEW' :
    scrapeResults.platform  // ← GOOGLE_ADS 등은 표시 안 됨
}
```

### 문제점 3: captured_at 포맷팅 오류

```typescript
<td className="py-3 px-4 text-gray-500 text-xs">
    {new Date(result.captured_at).toLocaleString('ko-KR')}
</td>
```

**문제**: 만약 captured_at이 ISO 8601 형식이 아니면?
```javascript
new Date("2026-02-20 10:30:00")  // ❌ 일부 브라우저에서 Invalid Date
new Date("2026-02-20T10:30:00Z") // ✅ 모든 브라우저에서 작동
```

### 문제점 4: 에러 상태 미처리

```typescript
// ❌ has_data === null 또는 results === null인 경우 처리 안 함
if (scrapeResults.has_data && scrapeResults.results.length > 0) {
    // 성공
} else {
    // 실패? 데이터 없음? 구분 불가
}

// 만약 scrapeResults 자체가 null이면?
{scrapeResults.has_data && ...}  // ✅ 안전
{scrapeResults.results.slice(0, 5) ...}  // ❌ null.results → TypeError!
```

### 해결 방법

```typescript
// 1. Platform 맵 생성 (상수)
const PLATFORM_NAMES: Record<string, string> = {
    'NAVER_PLACE': '네이버 플레이스',
    'NAVER_VIEW': '네이버 VIEW',
    'GOOGLE_ADS': '구글 광고',
    'META_ADS': '메타 광고',
};

// 2. 안전한 날짜 포맷팅
const formatDate = (dateString: string) => {
    try {
        return new Date(dateString).toLocaleString('ko-KR');
    } catch {
        return dateString;
    }
};

// 3. 표시 개수 동적 조정
const DISPLAY_COUNT = Math.min(10, scrapeResults.results.length);

// 4. null 체크 강화
if (!scrapeResults || !scrapeResults.results) {
    return <ErrorState message="결과를 불러올 수 없습니다." />;
}
```

---

## 📊 15가지 문제점 전체 요약

| # | 문제 | 심각도 | 카테고리 | 수정 난이도 |
|---|------|--------|----------|-----------|
| 1 | NEXT_PUBLIC_API_URL | 🔴 | 배포 | 낮음 |
| 2 | Docker 런타임 환경변수 | 🔴 | 배포 | 낮음 |
| 3 | API 라우팅 경로 | 🟡 | 라우팅 | 낮음 |
| 4 | UUID 검증 실패 | 🟡 | 데이터 | 낮음 |
| 5 | 스크래핑 대기 시간 | 🟡 | 비동기 | 중간 |
| 6 | 에러 무시 | 🔴 | 에러처리 | 중간 |
| 7 | 인증 미검증 | 🔴 | 보안 | 낮음 |
| 8 | BackgroundTasks | 🔴 | 아키텍처 | 높음 |
| 9 | 작업 추적 불가 | 🟠 | 모니터링 | 중간 |
| 10 | 검증 지연 | 🟠 | UX | 낮음 |
| 11 | rank_change 미구현 | 🔴 | 데이터 | 낮음 |
| 12 | 세션 누수 | 🔴 | 리소스 | 낮음 |
| 13 | toast 메시지 | 🟡 | UX | 중간 |
| 14 | 동시 요청 | 🟡 | 동시성 | 중간 |
| 15 | 컴포넌트 제한 | 🟠 | UX | 낮음 |

---

## 🎯 우선순위 재정의 (15개 기준)

### Phase 1: 긴급 수정 (1-2시간)
1. **문제점 1, 2**: Dockerfile & GitHub Actions 환경변수
2. **문제점 7**: scrape 엔드포인트 인증 추가
3. **문제점 11**: rank_change 필드 추가
4. **문제점 12**: db.rollback() 추가

### Phase 2: 높은 우선순위 (4-6시간)
5. **문제점 5**: 동적 대기 시간
6. **문제점 6**: 에러 처리 강화
7. **문제점 14**: 동시 요청 방지

### Phase 3: 보완 (6-8시간)
8. **문제점 8**: BackgroundTasks → Cloud Tasks
9. **문제점 13**: toast 메시지 개선
10. **문제점 15**: 컴포넌트 개선

### Phase 4: 최적화 (후속)
11. **문제점 3, 4, 9, 10**: 문서화 및 개선

---

**총 수정 예상 시간**: 16-24시간
**팀 규모**: 2명 (프론트엔드 1명, 백엔드 1명)
**병렬 작업**: 최대 4개 문제점 동시 작업 가능

