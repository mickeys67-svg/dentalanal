# 🗓️ 세션 핸드오프 — 2026-07-04 (오전)

> 오후에 이어서 하기 위한 진행 상황·다음 할 일 정리.
> 상세 현황은 [PROJECT_STATUS.md](./PROJECT_STATUS.md) 참조.

---

## 1. 지금 라이브 상태 (전부 검증 완료)

| 항목 | 값 |
|------|-----|
| 프론트 | https://dentalanal-531022561413.us-west1.run.app |
| 백엔드 | https://dentalanal-backend-hncihcsqta-uw.a.run.app |
| 로그인 | `admin` / `admin123!` |
| 백엔드 리비전 | `dentalanal-backend-00008-pnn` |
| Git | `main` = `origin/main` = `2272761` (동기화됨) |

### ✅ 실데이터로 작동 (10회 UX 시뮬레이션 10/10 통과)
- 로그인 / 인증
- **키워드 검색량** (네이버 키워드도구) — 다중, 차트·상세·워드클라우드·CSV·최초검색일
- **검색 트렌드 / 성별·연령** (네이버 데이터랩) — 추이 라인차트, 월별/요일별, "상대지수" 정직 배너
- **유튜브 언급량** (YouTube Data API v3) — KPI·이중축 월별차트 (오늘 활성화)

### 🟡 정직한 "미연동" 상태 (가짜 제거 완료, 외부 소스 필요)
- Meta/Google 광고 성과 → 광고계정 토큰 필요 (RFP 핵심 아님 = 보류키로 함)
- 감성분석 → LLM 키(`ANTHROPIC_API_KEY`) 필요
- 업종 벤치마크 → ① 광고 연동 후 자사데이터 집계가 유일한 정답
- X/인스타/틱톡 → API 제약 (유료/벤더)

---

## 2. 오늘 한 것 (커밋 이력)

| 커밋 | 내용 |
|------|------|
| `2272761` | deploy-keys.env gitignore 확정 + 프리뷰 launch.json |
| `02b2176` | 유튜브 언급량 실데이터 활성화 |
| `03facf6` `e6889ee` | ROI 가정값 투명화 + 사이드바 제품 포커스 정리 |
| `6c04806` | 미연동 빈영역 전문안내 ConnectPrompt |
| `9ceb972` | 로그인 UI 관문 수정 + 가짜 데이터 제거(NO FAKE DATA) |
| `349d964` | 키워드도구 견고성(배치격리+429 내성) |

**핵심 성과**: 로그인 관문 버그 수정, 광고비추정 네이버 실연동, 랜덤/고정 가짜 전면 제거, 유튜브 활성화, 사이드바 정리, 데이터랩 활성화.

---

## 3. 오후에 할 일 (우선순위)

### A. 감성분석 실연동 (제일 쉬움 — 키 하나)
- `ANTHROPIC_API_KEY`를 `deploy-keys.env`에 넣으면 → 실제 언급 텍스트 기반 감성분류 구현
- 넣는 곳: `deploy-keys.env`의 `ANTHROPIC_API_KEY=` 슬롯 (이미 있음)

### B. UX 미세 다듬기 (시뮬에서 발견)
- [ ] 로그인 좌측 브랜딩 패널 `lg:`(1024px) → `md:`로 낮춰 태블릿에서도 노출
- [ ] 유튜브 "영상수(근사) 1,000,000" 카드 흐리게/재배치 (조회수 중심)

### C. Meta 광고 (원하면) — per-client 아키텍처
- 이미 DB 구조 존재(`PlatformConnection.client_id + credentials`)
- 광고 서비스가 per-client 자격증명 읽도록 전환 + 자격증명 암호화 + 연동 화면
- ⚠️ 결정 보류 중 (RFP 핵심은 키워드·SNS라 우선순위 낮음)

### D. roi_optimizer 잔여
- `ASSUMED_CONVERSION_VALUE` 가정 ROAS는 배너로 투명화 완료. 추가로 전환수익 설정 UI 강제 검토.

---

## 4. 재개 방법 (명령어)

### 배포 (로컬 소스 직접 — GitHub 트리거 쓰지 말 것)
```powershell
# 백엔드
gcloud run deploy dentalanal-backend --source "E:\dentalanal\backend" --project snsproject-501311 --region us-west1 --allow-unauthenticated --port 8080 --cpu 1 --memory 2Gi --timeout 600
# 프론트
gcloud run deploy dentalanal --source "E:\dentalanal\frontend" --project snsproject-501311 --region us-west1 --allow-unauthenticated --port 8080
# env 주입(재빌드 없이): gcloud run services update dentalanal-backend ... --update-env-vars "KEY=값"
```

### 로컬 프리뷰 (UX 확인)
- `.claude/launch.json`(frontend-dev, port 3000) + `frontend/.env.local`(백엔드 URL) 이미 준비됨
- Preview로 `frontend-dev` 시작 → 데스크톱(1280) 리사이즈해서 봐야 브랜딩 패널 보임

### Git push
```powershell
cd E:\dentalanal; .\git-push.ps1     # .github_token 사용, GCM 우회
```

---

## 5. 크리덴셜 현황 (gitignore됨 — 리포에 안 올라감)
- `deploy-keys.env`: NAVER_CLIENT_ID/SECRET, YOUTUBE_API_KEY(실키 들어있음), Meta/Google/ANTHROPIC 빈 슬롯
- `.github_token`: GitHub PAT (⚠️ 채팅 노출 이력 있어 회전 권장)
- ⚠️ 유튜브 키도 채팅 노출됨 → 콘솔에서 API 제한/회전 권장

---

**요약**: 핵심 제품(키워드·트렌드·SNS)은 실데이터로 "잘 만들었네" 수준 완성·검증됨. 오후엔 감성분석 키 연동(A) + UX 미세조정(B)부터 하면 됨.
