# 🏥 DentalAnal 마케팅 대시보드 - 개발 가이드

> **Claude 에이전트 및 개발자를 위한 프로젝트 가이드**
>
> 이 문서는 DentalAnal 프로젝트의 전체 비전, 현재 진행 상황, 그리고 향후 개발 방향을 정의합니다.

---

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [현재 완료된 Phase](#현재-완료된-phase)
3. [기술 스택 및 아키텍처](#기술-스택-및-아키텍처)
4. [다음 단계 개발 방향](#다음-단계-개발-방향)
5. [개발 가이드라인](#개발-가이드라인)

---

## 🎯 프로젝트 개요

### 목적
치과 마케팅 대행사 및 병원을 위한 **올인원 마케팅 인텔리전스 플랫폼**

### 핵심 가치 제안
1. **통합 데이터 수집**: 네이버 광고, 플레이스, 블로그 등 모든 마케팅 채널을 한눈에
2. **실시간 인사이트**: 경쟁사 분석, 순위 추적, ROI 최적화
3. **자동화된 리포팅**: 클라이언트 보고서 자동 생성 및 발송

### 타겟 사용자
- **1차**: 치과 마케팅 대행사 (Agency)
- **2차**: 자체 마케팅 운영 치과 병원 (Direct Client)

---

## ✅ 현재 완료된 Phase

### Phase 1: 프리미엄 UI 구축 ✓
**완료일**: 2026-02-17

**주요 성과**:
- shadcn/ui 기반 현대적 컴포넌트 시스템 구축
- 대시보드 레이아웃 재구성 (`(authenticated)` 그룹)
- 7개 프리미엄 대시보드 컴포넌트 추가:
  - CompetitorComparison (경쟁사 비교)
  - KeywordRankTable (키워드 순위 테이블)
  - KeywordSummary (키워드 요약)
  - MentionFeed (언급 피드)
  - ScoreCard (성과 카드)
  - SentimentGauge (감성 분석 게이지)
  - DashboardEmptyState (빈 상태 처리)

**새 페이지**:
- `/dashboard/ads` - 광고 종합 대시보드
- `/dashboard/place` - 네이버 플레이스 분석
- `/dashboard/viral` - 바이럴 마케팅 분석

**기술 스택**:
- Next.js 14 (App Router)
- shadcn/ui + Radix UI
- Tailwind CSS
- TypeScript

### Phase 2: 안정적 데이터 수집 ✓
**완료일**: 2026-02-17

**주요 성과**:
- Naver Search API 공식 통합 (`backend/app/external_apis/naver_search.py`)
- 3단계 데이터 소스 폴백 시스템:
  1. RECONCILED (최우선 - 정합성 검증 완료)
  2. API (공식 API 데이터)
  3. SCRAPER (스크래핑 데이터)
- 스크래핑 안정성 개선 (재시도 로직, 에러 핸들링)
- 샘플 데이터 시딩 기능 (`/api/v1/status/seed-test-data`)

**데이터 수집 채널**:
- ✅ Naver Ads API (광고 성과)
- ✅ Naver Search API (검색 순위)
- ✅ Naver Place Scraper (플레이스 순위)
- ✅ Naver View Scraper (블로그 순위)

### Phase 3: 시스템 안정화 ✓
**완료일**: 2026-02-17

**주요 성과**:
- 스케줄러 안정화 (`backend/app/core/scheduler.py`)
- 구조화된 로깅 시스템 (`backend/app/core/logger.py`)
- Cloud Run 배포 최적화 (IPv4/Domain 연결)
- 개발용 코드 대청소 (8,371줄 삭제):
  - 테스트 스크립트 제거
  - 디버그 HTML 파일 정리
  - SQLite 폴백 로직 제거

**인프라**:
- GitHub Actions 자동 배포
- Supabase (PostgreSQL) 단일 데이터베이스
- Cloud Run (서버리스)

---

## 🛠 기술 스택 및 아키텍처

### Frontend Stack
```
Next.js 14 (App Router)
├── shadcn/ui (Component Library)
├── Radix UI (Primitives)
├── Tailwind CSS (Styling)
├── TypeScript (Type Safety)
└── React Query (Data Fetching) - [예정]
```

### Backend Stack
```
FastAPI
├── SQLAlchemy (ORM)
├── Supabase/PostgreSQL (Database)
│   ├── 정형 데이터 (Relational Tables)
│   └── 비정형 데이터 (JSONB Columns)
├── Pydantic (Validation)
└── APScheduler (Task Scheduling)
```

### Data Collection Stack
```
Official APIs
├── Naver Ads API (광고 성과)
└── Naver Search API (검색 순위)

Scrapers (Fallback)
├── Naver Place Scraper
└── Naver View Scraper
```

### Infrastructure
```
Cloud Platform
├── Backend: Google Cloud Run
├── Database: Supabase (PostgreSQL)
├── CI/CD: GitHub Actions
└── Domain: [TBD]
```

### 핵심 아키텍처 원칙

**1. 단일 데이터 소스 (Single Source of Truth)**
- Supabase (PostgreSQL)를 모든 데이터의 유일한 저장소로 사용
- MongoDB, SQLite 등 다른 DB는 사용하지 않음
- 비정형 데이터는 JSONB 컬럼 활용

**2. 데이터 정합성 우선 (Reconciliation First)**
```
수집 파이프라인:
API 데이터 →
Scraper 데이터 →
Reconciliation Engine →
RECONCILED (최종 데이터) →
Dashboard 노출
```

**3. 타임존 고정 (KST Only)**
- 모든 시간 데이터는 한국 시간(UTC+9) 기준
- 광고 데이터 수집/표시 모두 KST 사용

---

## 🚀 다음 단계 개발 방향

### Phase 4: 고급 분석 및 인사이트 (우선순위 1)
**목표 기간**: 2026년 2월 말

**핵심 기능**:
1. **경쟁사 인텔리전스**
   - 자동 경쟁사 발굴 알고리즘
   - 경쟁사 광고 전략 분석
   - 키워드 포지셔닝 맵

2. **ROI 최적화 엔진**
   - 캠페인별 ROAS 추적
   - 비효율 광고 자동 감지
   - 예산 재분배 추천

3. **트렌드 분석**
   - 계절성 패턴 감지
   - 검색 트렌드 예측
   - 알림 시스템 (순위 급락, 예산 초과 등)

**기술 구현**:
- React Query 도입 (데이터 캐싱 및 실시간 업데이트)
- WebSocket 연결 (실시간 알림)
- Chart.js 또는 Recharts (고급 차트)

### Phase 5: 자동화된 리포팅 (우선순위 2)
**목표 기간**: 2026년 3월

**핵심 기능**:
1. **리포트 빌더**
   - 드래그 앤 드롭 위젯 시스템
   - 템플릿 갤러리
   - 화이트라벨 브랜딩

2. **자동 발송**
   - 주간/월간 리포트 자동 생성
   - 이메일 자동 발송
   - PDF 내보내기

3. **클라이언트 포털**
   - 읽기 전용 대시보드 공유
   - 맞춤형 인사이트 페이지

**기술 구현**:
- Puppeteer (PDF 생성)
- Nodemailer (이메일 발송)
- React DnD (드래그 앤 드롭)

### Phase 6: AI 기반 마케팅 어시스턴트 (우선순위 3)
**목표 기간**: 2026년 4월

**핵심 기능**:
1. **자동 광고 문구 생성**
   - 성과 좋은 문구 패턴 학습
   - A/B 테스트 문구 자동 생성

2. **챗봇 인사이트**
   - 자연어로 데이터 질의
   - "이번 달 가장 효율적인 키워드는?" → 자동 답변

3. **스마트 추천**
   - 최적 입찰가 제안
   - 타겟팅 최적화 제안

**기술 구현**:
- OpenAI API 또는 Claude API
- LangChain (RAG 시스템)
- Vector DB (임베딩 저장)

---

## 🧑‍💻 개발 가이드라인

### 코드 컨벤션

#### Backend (Python/FastAPI)
```python
# 파일명: snake_case
# 클래스명: PascalCase
# 함수/변수명: snake_case
# 상수: UPPER_SNAKE_CASE

# 예시:
class AnalysisService:
    def get_funnel_data(self, client_id: str) -> dict:
        SOURCE_PRIORITY = ['RECONCILED', 'API', 'SCRAPER']
        ...
```

**필수 원칙**:
- Type hints 사용 (모든 함수 파라미터 및 리턴 값)
- Docstring 작성 (복잡한 비즈니스 로직에 대해)
- 에러 핸들링 (try-except + 로깅)

#### Frontend (TypeScript/React)
```typescript
// 파일명: PascalCase (컴포넌트), camelCase (유틸)
// 컴포넌트명: PascalCase
// 함수/변수명: camelCase
// 상수: UPPER_SNAKE_CASE

// 예시:
export function AnalysisPage() {
  const [data, setData] = useState<AnalysisData | null>(null)
  const MAX_RETRIES = 3
  ...
}
```

**필수 원칙**:
- TypeScript strict mode 준수
- React Hooks 규칙 준수
- 컴포넌트 단위 파일 분리 (1 파일 = 1 컴포넌트)

### Git Workflow

#### 브랜치 전략
```
main (프로덕션)
  └── develop (통합 개발)
       ├── feature/xxx (새 기능)
       ├── fix/xxx (버그 수정)
       └── refactor/xxx (리팩토링)
```

#### 커밋 메시지 규칙
```
[Type] 제목 (한글, 50자 이내)

- 상세 설명 (선택)
- 변경 이유 및 영향

Type:
- [Feat]: 새 기능
- [Fix]: 버그 수정
- [Refactor]: 리팩토링
- [Dev]: 개발 도구/설정
- [Cleanup]: 코드 정리
- [Build]: 빌드/배포
- [Hotfix]: 긴급 수정

예시:
[Feat] 경쟁사 자동 발굴 알고리즘 구현

- CompetitorDiscoveryService 추가
- 키워드 중복도 기반 유사 타겟 식별
- 대시보드에 추천 경쟁사 섹션 추가
```

### PR 프로세스

#### PR 생성 시
1. **제목**: `[Type] 간결한 설명`
2. **본문**:
   ```markdown
   ## 변경 사항
   - 항목 1
   - 항목 2

   ## 테스트 방법
   1. ...
   2. ...

   ## 스크린샷 (UI 변경 시)
   [첨부]

   ## 체크리스트
   - [ ] 로컬 테스트 완료
   - [ ] 타입 에러 없음
   - [ ] 린트 통과
   - [ ] 관련 문서 업데이트
   ```

#### 리뷰 기준
- ✅ 기능 동작 확인
- ✅ 코드 가독성
- ✅ 에러 핸들링
- ✅ 성능 영향
- ✅ 보안 이슈

### 테스트 정책

#### 현재 상태
- ⚠️ 단위 테스트 미구현 (기술 부채)
- ⚠️ E2E 테스트 미구현 (기술 부채)

#### Phase 4 이후 도입 예정
```python
# Backend: pytest
def test_get_funnel_data():
    service = AnalysisService(mock_db)
    result = service.get_funnel_data(client_id="test")
    assert result["items"][0]["stage"] == "노출 (Impressions)"
```

```typescript
// Frontend: Vitest + React Testing Library
describe('AnalysisPage', () => {
  it('renders funnel chart', () => {
    render(<AnalysisPage />)
    expect(screen.getByText('전환 퍼널')).toBeInTheDocument()
  })
})
```

---

## 🔧 기술 부채 및 개선 항목

### 긴급 (Phase 4 이전 해결)
- [ ] **Frontend 에러 바운더리 추가** (전체 앱 크래시 방지)
- [ ] **API 응답 타입 정의** (백엔드-프론트엔드 계약)
- [ ] **환경변수 검증** (누락 시 명확한 에러 메시지)

### 중요 (Phase 5 이전 해결)
- [ ] **단위 테스트 도입** (핵심 비즈니스 로직)
- [ ] **DB 마이그레이션 관리** (Alembic 도입)
- [ ] **캐싱 전략** (Redis 도입 고려)

### 일반 (장기)
- [ ] **E2E 테스트** (Playwright)
- [ ] **성능 모니터링** (Sentry, DataDog)
- [ ] **로드 테스트** (Locust)

---

## 📚 참고 문서

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 기술 스택 상세 설명
- [README.md](./README.md) - 프로젝트 개요 및 설치 가이드
- [DEPLOYMENT_V2.md](./DEPLOYMENT_V2.md) - 배포 가이드

---

## 🤝 기여 가이드

### 새 기능 제안
1. GitHub Issues에 `[Feature Request]` 라벨로 등록
2. 사용자 스토리 작성 ("~으로서, ~를 원한다, ~하기 위해")
3. 팀 논의 후 우선순위 결정

### 버그 리포트
1. GitHub Issues에 `[Bug]` 라벨로 등록
2. 재현 방법, 기대 동작, 실제 동작 명시
3. 스크린샷 또는 로그 첨부

---

## 📞 연락처

프로젝트 관련 문의: [담당자 정보 추가 필요]

---

**최종 업데이트**: 2026-02-17
**다음 리뷰 예정**: Phase 4 시작 시점
