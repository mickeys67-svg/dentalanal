# 🚀 D-MIND 플랫폼 통합 배포 가이드

이 문서는 D-MIND 플랫폼을 프로덕션 환경에 배포하기 위한 모든 정보를 담고 있습니다.

## 1. 배포 대상 플랫폼별 가이드

### 옵션 A: Render (가장 추천)
Render는 GitHub 연동을 통해 백엔드(Python), 프론트엔드(Next.js), DB(Postgres), Redis를 한 번에 관리할 수 있습니다.

1.  **파일**: `render.yaml`을 사용합니다.
2.  **방법**: 
    - Render 대시보드에서 `Blueprints` 메뉴로 이동합니다.
    - 이 리포지토리를 연결하면 `render.yaml`을 인식하여 모든 서비스가 자동으로 생성됩니다.
    - **주의**: 고성능 스크래핑을 위해 백엔드는 Docker 환경으로 설정되어 있습니다.

### 옵션 B: Google Cloud Run (확장성 중심)
대규모 트래픽 대응 및 확장성이 필요한 경우 GCP를 사용합니다.

1.  **파일**: `deploy_gcp.ps1` (Windows용) 및 `.github/workflows/deploy.yml` (자동화)
2.  **방법**: 
    - `gcloud` CLI가 설치된 환경에서 `.\deploy_gcp.ps1`을 실행합니다.
    - GitHub에 Push하면 자동으로 Cloud Run에 배포됩니다.

### 옵션 C: Docker Compose (단독 서버/로컬)
개별 리눅스 서버(Ubuntu 등)에 직접 배포할 때 사용합니다.

1.  **파일**: `docker-compose.yml`
2.  **방법**: 
    ```bash
    docker-compose up -d --build
    ```
    - 모든 서비스가 컨테이너화되어 실행되며, 프론트엔드(3000), 백엔드(8000) 포트로 접속 가능합니다.

---

## 2. 필수 환경 변수 (ENV) 설정

배포 시 플랫폼 설정 메뉴에서 반드시 다음 변수들을 입력해야 합니다.

| 구분 | 변수명 | 설명 |
|---|---|---|
| **Common** | `DATABASE_URL` | 데이터베이스 접속 주소 (Render 사용 시 자동생성) |
| | `REDIS_URL` | 리스 큐 접속 주소 (Render 사용 시 자동생성) |
| **Backend** | `GOOGLE_API_KEY` | Gemini AI 연동을 위한 Google AI SDK 키 |
| | `GOOGLE_ADS_DEVELOPER_TOKEN` | (선택) Google Ads API 연동 시 필요 |
| **Frontend** | `NEXT_PUBLIC_API_URL` | 백엔드 API 서버의 공개 URL |

---

## 3. 사후 관리 및 모니터링
- **상태 확인**: `/api/v1/status/status` 엔드포인트를 통해 시스템의 생동감을 확인할 수 있습니다.
- **로그**: 각 플랫폼의 로그 스트림(Render Logs, Cloud Logging 등)을 통해 에러를 추적하세요.

배포 관련 문의사항이 있으시면 언제든지 말씀해 주세요!
