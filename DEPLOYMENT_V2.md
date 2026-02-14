# 🚀 D-MIND 플랫폼 통합 배포 가이드 (V2)

이 문서는 최신화된 D-MIND 플랫폼 배포 절차를 설명합니다.

## 1. 전제 조건
- **GitHub**: 최신 코드가 GitHub에 푸시되어 있어야 합니다.
- **환경 변수**: `backend/.env` 및 플랫폼별 시크릿 설정이 필요합니다.

---

## 2. 배포 방법

### 방법 A: Docker Compose (단독 서버/로컬 테스트)
가장 빠르고 간편하게 전체 시스템을 구동하는 방법입니다.
```bash
# 빌드 및 실행
docker-compose up -d --build

# 상태 확인
docker-compose ps
```

### 방법 B: Google Cloud Run (확장형/GCP)
고성능 및 자동 확장성이 필요한 경우 사용합니다.
1. `gcloud auth login` 으로 인증
2. `.\deploy.ps1` 실행 (Windows PowerShell 전용)

### 방법 C: Render (GitHub 연동형)
GitHub에 푸시하는 것만으로 자동 배포하고 싶은 경우 사용합니다.
- `render.yaml` 설정을 통해 Render 대시보드에서 Blueprint를 생성하세요.

---

## 3. GitHub 동기화 이슈 해결
만약 `git push` 인증 오류가 발생한다면, 아래 명령어로 리모트 URL을 재설정하세요:
```bash
git remote set-url origin https://<YOUR_TOKEN>@github.com/mickeys67-svg/dentalanal.git
git push origin main
```

---

## 4. 사후 검증
배포 후 `python verify_api.py`를 실행하여 핵심 기능(로그인, 클라이언트 생성 등)이 정상 작동하는지 확인하세요.
