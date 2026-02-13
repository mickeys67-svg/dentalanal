# 🏥 DentalAnal Project: Master Architecture & Standards

이 문서는 프로젝트의 핵심 기술 스택과 아키텍처 원칙을 정의합니다. **모든 개발 작업 및 AI 에이전트는 작업을 시작하기 전 이 문서를 반드시 숙지해야 합니다.**

## 1. 핵심 데이터베이스 스택 (Hybrid DB Stack)

본 프로젝트는 데이터의 성격에 따라 두 종류의 데이터베이스를 혼합하여 사용합니다.

### 🗄️ Supabase (PostgreSQL) - "The Source of Truth"
- **용도**: 모든 정형 데이터, 사용자 정보, 광고 성과 지표(Metrics), 캠페인 정보, 결제 상태.
- **특징**: `app/core/database.py`에서 `DATABASE_PASSWORD`가 존재할 경우 자동으로 활성화됩니다.
- **주의**: 운영 환경(Cloud Run)에서는 SQLite를 절대 사용하지 않으며, 모든 영속 데이터는 Supabase로 집중됩니다.

### 📜 MongoDB (Atlas) - "The Raw Intelligence Store"
- **용도**: 브라이트 데이터(Scraper)로 수집된 대용량 원본 HTML, JSON 응답값, 비정형 로그.
- **특징**: `MongoService`를 통해 관리됩니다. SQL DB의 비대화를 방지하고 분석의 유연성을 제공합니다.

---

## 2. 개발 및 수정 원칙 (Immutable Rules)

1. **DB 가시성 우선**: 모든 백엔드 수정 시 `app/core/config.py`의 DB URL 생성 로직을 먼저 확인해야 합니다.
2. **이중 저장 (Dual-Write)**: 분석 데이터 저장 시 반드시 SQL(정량)과 NoSQL(원본)에 동시 기록합니다.
3. **타임존 고정 (KST)**: 모든 광고 데이터 및 수집 시간은 한국 시간(`UTC+9`)을 기준으로 보정합니다.
4. **목업 데이터 제거**: 실제 API 연동이 완료된 모듈에서는 로컬 샘플/목업 데이터 로직을 점진적으로 제거하고 실제 DB 레코드를 사용합니다.

---

## 3. API 수집 안정성 솔루션 (Reconciliation Strategy)

데이터 유실과 부정확성을 방지하기 위해 **이중 수집 및 정합성 엔진**을 운용합니다.

### 🛡️ 수집 채널 분리
- **Official API (NaverAdsService)**: 정밀한 성과 데이터를 제공하는 기본 채널입니다. 지표의 정확성이 높으며 `source='API'`로 저장됩니다.
- **Bright Data Scraper (NaverAdsManagerScraper)**: API 권한 문제나 일시적 장애 시 작동하는 강력한 백업 채널입니다. `source='SCRAPER'`로 저장됩니다.

### ⚖️ 정합성 정책 (Reconciliation Policy)
두 채널에서 수집된 데이터는 `DataReconciliationService`를 통해 하나의 신뢰할 수 있는 데이터로 병합됩니다.
1. **우선순위**: API 데이터가 존재할 경우 이를 최우선으로 선택합니다.
2. **Fallback**: API 데이터가 비어있거나 오류가 있을 경우, Scraper 데이터를 선택합니다.
3. **최종 지표 (`RECONCILED`)**: 검증이 완료된 데이터는 `source='RECONCILED'` 태그를 달고 저장됩니다.
4. **대시보드 노출**: 프론트엔드 대시보드는 오직 `RECONCILED` 데이터만 조회합니다. (중복 합산 및 데이터 누락 원천 차단)

---

## 4. 에이전트 가이드 (For AI Assistants)

- 작업을 시작할 때 반드시 `backend/app/core/config.py`를 열어 현재 활성화된 DB 환경을 확인하십시오.
- 대화 세션이 바뀌어도 **Supabase**와 **MongoDB**가 이 프로젝트의 심장임을 잊지 마십시오.
- 새로운 필드를 추가할 때는 PostgreSQL(정형)에 넣을지 MongoDB(비정형)에 넣을지 아키텍처 설계 관점에서 판단하십시오.
