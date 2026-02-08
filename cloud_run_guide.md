# Google Cloud Run 배포 사양 가이드 (D-MIND)

Cloud Run은 서버리스 컨테이너 환경이므로, 기존 VM(Ubuntu)과 달리 **Stateless(데이터 저장 안 함)** 원칙을 따라야 합니다.

## 🚀 0. 배포 시작하기 (화면 가이드)
보내주신 스크린샷 화면에서 **[저장소 연결]** (GitHub 아이콘) 버튼을 누르세요. 이것이 가장 쉽고 강력한 배포 방법입니다.

### 왜 [저장소 연결] 인가요?
- 코드를 수정해서 GitHub에 올리면(Push), **자동으로 서버가 업데이트** 됩니다. (CI/CD 자동화)
- 별도로 이미지를 빌드해서 올릴 필요가 없습니다.

---

## ⚠️ 1. 시작 전 필수 준비물 (환경 변수)
**[저장소 연결]** 누르시기 전에 달성해야 할 **퀘스트**가 있습니다. 설정 도중에 아래 값들을 넣어야 하거든요.

1.  **DB 주소 (`DATABASE_URL`)**: Supabase나 Neon에서 받은 주소
2.  **Redis 주소 (`REDIS_URL`)**: Upstash에서 받은 주소
3.  **Google API Key (`GOOGLE_API_KEY`)**: 이미 가지고 계신 키

*이 3가지 주소가 메모장에 적혀 있나요? 없다면 먼저 가입해서 주소부터 받아와야 합니다!*

---

## 2. Cloud Run 서비스 설정 순서

### 1단계: Cloud Build 설정
1.  **저장소 연결** 클릭
2.  **공급자**: GitHub 선택
3.  **저장소**: `mickeys67-svg/dentalanal` 선택
4.  **다음** 클릭
5.  **브랜치**: `^main$` (기본값 유지)
6.  **Build Type**: `Dockerfile` 선택
    *   *(참고: 우리 프로젝트엔 백엔드/프론트엔드 각각 Dockerfile이 있으므로, 서비스 2개를 따로 만들어야 합니다. 우선 **백엔드**부터 해봅시다.)*
    *   **Source location**: `/backend` (백엔드 Dockerfile이 여기 있습니다)

### 2단계: 구성 (Configuration)
1.  **서비스 이름**: `d-mind-backend` (또는 원하시는 이름)
2.  **리전**: `asia-northeast3` (서울) 추천
3.  **인증**: "인증되지 않은 호출 허용" 체크 (외부에서 접속 가능하게)

### 3단계: 컨테이너, 볼륨, 네트워킹, 보안 (중요!)
이 탭을 열어서 사양을 조정해야 합니다.
1.  **리소스 할당**:
    *   CPU: `2`
    *   메모리: `4GiB` (스크래핑용)
2.  **환경 변수 (Environment variables)**: **여기가 제일 중요합니다!**
    *   [변수 추가] 버튼을 눌러서 아래 3개를 입력하세요.
    *   `DATABASE_URL` : (준비해둔 DB 주소)
    *   `REDIS_URL` : (준비해둔 Redis 주소)
    *   `GOOGLE_API_KEY` : (준비해둔 Gemini 키)
3.  **요청 시간 제한 (Timeout)**: `300` (초) 설정

**[만들기]** 버튼 클릭! 🚀

우리 서비스는 **브라우저 스크래핑(Playwright)**과 **AI 분석**을 수행하므로 메모리 리소스가 중요합니다.

### A. 백엔드 (Backend API & Worker)
스크래퍼(Chrome 브라우저) 실행을 위해 넉넉한 메모리가 필요합니다.
*   **CPU**: 2 vCPU 이상
*   **Memory**: **4GB (최소 2GB)**
*   **Concurrency**: 80 (기본값)
*   **Execution Environment**: 2세대 (Generation 2) 권장 (파일시스템 접근 등 호환성 좋음)
*   **특이사항**: 스크래핑이 오래 걸릴 수 있으므로 **Request Timeout**을 `300초(5분)` 이상으로 늘려야 합니다.

### B. 프론트엔드 (Frontend - Next.js)
단순 웹 호스팅 역할이므로 낮은 사양으로 충분합니다.
*   **CPU**: 1 vCPU
*   **Memory**: 512MB ~ 1GB

---

## 2. 필수 인프라 (Backing Services)

Cloud Run 내부의 파일은 재시작 시 사라지므로, 데이터는 외부에 저장해야 합니다.

### A. 데이터베이스 (PostgreSQL)
*   **서비스**: **Cloud SQL for PostgreSQL**
*   **버전**: PostgreSQL 15 또는 16
*   **사양**: `db-f1-micro` (개발/테스트용) 또는 `db-g1-small` (프로덕션 최소 사양)
    *   *비용 절감을 위해 "공유 코어" 인스턴스 사용 권장*

### B. 메시지 큐 (Redis)
Celery 작업을 위해 필요합니다.
*   **서비스**: **Cloud Memorystore for Redis** (기본 추천, 안정적, But 유료)
*   **대안 1 (무료/저렴)**: **Upstash Redis** (Serverless, 트래픽 적으면 무료)
*   **대안 2 (무료/저렴)**: **Redis Cloud** (30MB 무료 티어 제공)

---

## 3. 비용 절감형 구성 (추천)

Google Cloud의 유료 서비스(Cloud SQL, Memorystore)가 부담스럽다면, 외부의 **무료 티어** 서비스를 연결해서 쓸 수 있습니다. **코드 수정 없이** 환경 변수(`DATABASE_URL`, `REDIS_URL`)만 바꾸면 됩니다.

### 추천 조합 (월 $0 가능)
1.  **DB**: **Supabase** 또는 **Neon** (PostgreSQL 무료 제공)
2.  **Redis**: **Upstash** (Serverless Redis 무료 제공)
3.  **서버**: **Cloud Run** (월 200만 요청 무료)

이렇게 하면 초기 비용 없이 운영 가능합니다.

---

## 4. 배포 준비 체크리스트

1.  [ ] **GCP 프로젝트 생성** 및 결제 계정 연결
2.  [ ] **데이터베이스 생성** (Cloud SQL 또는 Supabase/Neon)
3.  [ ] **Redis 생성** (Memorystore 또는 Upstash)
    *   생성 후 `REDIS_URL` 확보 (예: `redis://default:password@...:6379`)
4.  [ ] **서비스 계정(Service Account) 생성** (Cloud SQL 사용 시)
5.  [ ] **도메인 연결** (선택 사항)

설정이 완료되면 **gcloud CLI**나 **GitHub Actions**를 통해 배포 스크립트를 짜드릴 수 있습니다.
**우선 위 사양대로 Cloud SQL과 Memorystore(또는 대안)를 생성해주세요.**
