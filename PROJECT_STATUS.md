# KeywordLens — 프로젝트 현황

> 키워드·SNS 통합 분석 어드민 (내부 마케팅용). 구 명칭: DentalAnal / D-MIND.
> 최종 갱신: 2026-07-04

---

## 1. 서비스 접속

| 항목 | 값 |
|------|-----|
| 프론트엔드 URL | https://dentalanal-531022561413.us-west1.run.app |
| 백엔드 URL | https://dentalanal-backend-hncihcsqta-uw.a.run.app |
| 로그인 아이디 | `admin` |
| 로그인 비밀번호 | `admin123!` |

---

## 2. 인프라

| 구성 | 내용 |
|------|------|
| GCP 프로젝트 | **snsproject-501311** (번호 531022561413), region **us-west1** |
| 백엔드 서비스 | Cloud Run `dentalanal-backend` |
| 프론트 서비스 | Cloud Run `dentalanal` |
| DB | Supabase `pgdphbpuxauldfunelxp` (pooler 연결. **direct 5432는 Cloud Run에서 IPv6라 불가 → pooler 사용**) |
| gcloud 기본 프로젝트 | `talktics` → 배포 시 `--project snsproject-501311` 명시 필수 |

> ⚠️ 구 인프라(GCP `dentalanal`, Supabase `xklppnykoeezgtxmomrl`)는 **삭제됨**. 위 새 인프라로 이전 완료.

---

## 3. 재배포 방법 (로컬 소스 직접 배포)

> GitHub 연결 Cloud Build 트리거(`rmgpgab-...`)는 루트 Dockerfile이 없어 **항상 실패** → 사용하지 말 것. 아래 CLI 사용.

**프론트엔드**
```powershell
gcloud run deploy dentalanal --source "E:\dentalanal\frontend" --project snsproject-501311 --region us-west1 --allow-unauthenticated --port 8080
```

**백엔드** (env는 scratchpad의 `backend-env.yaml`)
```powershell
gcloud run deploy dentalanal-backend --source "E:\dentalanal\backend" --project snsproject-501311 --region us-west1 --allow-unauthenticated --port 8080 --cpu 1 --memory 2Gi --timeout 600 --env-vars-file "<scratchpad>\backend-env.yaml"
```

---

## 4. 기능 현황

### ✅ 실데이터로 작동 (프로덕션 검증 완료)
- 로그인 / 인증
- **키워드 검색량** (1~10개 다중, 네이버 검색광고 키워드도구 API) — 월간검색수 PC/모바일
- **연관키워드**
- **최초 검색일** 영속화 (`keyword_search_stats` 테이블)
- **마스킹 정직 처리** (검색수 10 미만 → `< 10`, 상수 위장 없음)
- 엑셀(CSV) 다운로드

### ⚠️ 코드는 준비됨, API 키 주입 필요
| 기능 | 필요 키 |
|------|---------|
| 검색 트렌드 / 성별·연령 / 월별·요일별 (데이터랩) | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` |
| 유튜브 영상수/조회수 | `YOUTUBE_API_KEY` |

→ 백엔드 재배포 시 `--env-vars-file`(backend-env.yaml)에 추가하면 활성화.

### ⛔ 미구현 (벤더/예산 결정 대기)
- 인스타그램 / 엑스(X) / 틱톡 언급량 — 공식 API 제약. `/sns/status`가 "키 필요/벤더 필요"로 정직 표기.

---

## 5. 정밀 시뮬레이션 결과 (10/10 PASS, 2026-07-03)

| # | 시나리오 | 결과 |
|---|----------|:----:|
| 1 | 로그인 | ✅ |
| 2 | 단일 키워드 검색 (다이어트 44,140/월) | ✅ |
| 3 | 다중 키워드 5개 동시 | ✅ |
| 4 | 연관 키워드 | ✅ |
| 5 | 최초검색일 영속화 | ✅ |
| 6 | 마스킹 정직 처리 | ✅ |
| 7 | 최대 10개 키워드 | ✅ |
| 8 | 검색 트렌드 → 503 정직 반환(키 미설정) | ✅ |
| 9 | 유튜브 → 503 정직 반환(키 미설정) | ✅ |
| 10 | SNS상태 API + 프론트 렌더 | ✅ |

---

## 6. 리브랜딩 (KeywordLens, 2026-07-04)

- 제품명 **D-MIND / Dental Analytics → KeywordLens** 전면 교체
- 치과/병원/의료 특화 카피 → 범용 마케팅 용어 (프론트 38파일 + 백엔드 서비스 9파일)
- 대행사/정산 **기능은 유지**, 문구만 중립화 (광고주 → 프로젝트/브랜드)
- 프론트 타입체크 ✅ / 백엔드 컴파일 ✅ / 사용자노출 잔여 0

---

## 7. 알려진 이슈 / 남은 작업

### 🔴 잔존 가짜 데이터 (NO FAKE DATA — 실연동 필요)
리브랜딩 중 발견. 문구는 범용화했으나 **값은 여전히 가짜**:
- `backend/app/services/competitor_service.py` `estimate_ad_spend` — 임의 cpc/volume (→ 네이버 키워드도구로 교체 가능)
- `backend/app/services/report_builder.py` BENCHMARK — 업종평균 고정값(2.5 / 800 / 3.2)
- `backend/app/services/meta_ads.py` — 목업 캠페인
- 일부 대시보드 목업 (SentimentGauge 등)

### ✅ 견고성 수정 완료 (2026-07-04, 대규모 시뮬레이션 발견 → 수정·재배포·재검증)
`naver_keyword_tool.py`, Cloud Run revision `dentalanal-backend-00004-bd9`:
- **배치 격리**: 이모지/특수문자 한 개가 네이버 400을 유발해도 배치 전체가 502로 죽지 않고, 해당 키워드만 `no_data`로 격리. (유효 3 + 이모지 1 → 유효 3 생존 검증)
- **동시성 429 내성**: 세마포어(동시 2) + 429 지수 백오프. 이전 동시 8건 중 3건 502 → 수정 후 8/8 성공.

### 기타
- **admin 시딩 버그**: `run_startup_tasks`가 fire-and-forget이라 시딩 실패가 조용히 사라짐 (현재는 수동 시딩됨). 근본 수정 권장.
- **GitHub 미푸시**: 로컬 커밋 `f82976c` 등 3커밋이 origin/main(`1631b88`)보다 앞섬. 푸시 대기.
- 데이터랩·유튜브 키 주입 시 시뮬 #8·#9가 실데이터로 전환됨.

---

## 8. Git 상태

```
로컬 main:   f82976c  [Refactor] KeywordLens 리브랜딩
             4ac5e13  Merge origin/main
             d9d2034  [Feat] SNS 키워드 인텔리전스
origin/main: 1631b88  (로컬이 3커밋 앞섬 — 푸시 필요)
```

---

## 9. 주요 코드 위치

| 기능 | 파일 |
|------|------|
| 네이버 키워드도구 | `backend/app/external_apis/naver_keyword_tool.py` |
| 데이터랩 트렌드 | `backend/app/external_apis/naver_datalab.py` |
| 유튜브 | `backend/app/external_apis/youtube_api.py` |
| 키워드 API | `backend/app/api/endpoints/keywords.py` |
| SNS API | `backend/app/api/endpoints/sns.py` |
| 키워드 검색량 화면 | `frontend/src/app/(authenticated)/dashboard/keywords/page.tsx` |
| 검색 트렌드 화면 | `frontend/src/app/(authenticated)/dashboard/trends/page.tsx` |
| SNS 화면 | `frontend/src/app/(authenticated)/dashboard/sns/page.tsx` |
