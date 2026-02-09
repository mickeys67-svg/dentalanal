# Ubuntu 24.04 배포 가이드 (D-MIND)

이 문서는 D-MIND 시스템을 Ubuntu 24.04 서버에 배포하기 위한 상세 단계를 가이드합니다.

## 1. 사전 준비 사항
Ubuntu 24.04 LTS 서버가 준비되어 있어야 하며, SSH 접속이 가능해야 합니다.

## 2. 필수 패키지 설치
서버에 접속한 후 다음 명령어를 실행하여 Docker 및 필요한 도구들을 설치합니다.

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
sudo apt install -y docker.io docker-compose git

# Docker 서비스 활성화
sudo systemctl enable --now docker
```

## 3. 프로젝트 코드 가져오기
GitHub 리포지토리가 준비되면 다음 명령어로 코드를 내려받습니다.

```bash
git clone [리포지토리_URL]
cd google-dentalanal
```

## 4. 환경 변수 설정
`.env` 파일을 생성하여 필요한 정보를 입력합니다. (비공개 키 포함)

```bash
# Backend 설정
nano backend/.env
# 아래 내용 입력 후 저장 (Ctrl+O, Enter, Ctrl+X)
# DATABASE_URL=postgresql://user:password@db:5432/dmind
# REDIS_URL=redis://redis:6379/0
# OPENAI_API_KEY=성공적으로_발급받으신_키_입력
```

## 5. Docker Compose 실행
Docker를 사용하여 전체 시스템(백엔드, 프론트엔드, DB, Redis)을 일괄 실행합니다.

```bash
# 전체 빌드 및 백그라운드 실행
sudo docker-compose up -d --build
```

## 6. 서비스 접속 및 확인
- **대시보드**: `http://서버_IP:3000`
- **백엔드 API**: `http://서버_IP:8000/docs`

## 7. 주요 관리 명령어
- 컨테이너 상태 확인: `sudo docker ps`
- 로그 확인: `sudo docker-compose logs -f backend`
- 시스템 재시작: `sudo docker-compose restart`
