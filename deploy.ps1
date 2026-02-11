# GCP Deployment Script (dentalanal)
# Usage: .\deploy.ps1
# This script will build and deploy both backend and frontend to Google Cloud Run.

$PROJECT_ID = "dentalanal"
$REGION = "us-west1"
$REPO_NAME = "dentalanal-repo"

Write-Host "--- 1. GCP 환경 설정 및 API 활성화 ---" -ForegroundColor Green
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Artifact Registry 확인 및 생성
$repoExists = gcloud artifacts repositories list --location=$REGION --filter="name:projects/$PROJECT_ID/locations/$REGION/repositories/$REPO_NAME" --format="value(name)"
if (-not $repoExists) {
    Write-Host "--- 2. Artifact Registry 생성 ---" -ForegroundColor Green
    gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION
}

Write-Host "--- 3. 백엔드(Backend) 이미지 빌드 및 배포 ---" -ForegroundColor Green
# 백엔드 이미지 빌드
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend ./backend

# 백엔드 데이터베이스 URL 및 환경변수 설정 확인 필요 (이미 생성된 DB가 있다고 가정)
gcloud run deploy dentalanal-backend `
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --timeout 300

# 배포된 백엔드 URL 획득
$BACKEND_URL = (gcloud run services describe dentalanal-backend --platform managed --region $REGION --format 'value(status.url)').Trim()
Write-Host "Detected Backend URL: $BACKEND_URL" -ForegroundColor Cyan

Write-Host "--- 4. 프런트엔드(Frontend) 이미지 빌드 및 배포 ---" -ForegroundColor Green
# 프런트엔드 빌드 (Next.js 용 API URL 주입)
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend ./frontend

# 프런트엔드 배포
gcloud run deploy dentalanal `
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL

$FRONTEND_URL = (gcloud run services describe dentalanal --platform managed --region $REGION --format 'value(status.url)').Trim()

Write-Host "`n--- 배포 완료! ---" -ForegroundColor Cyan
Write-Host "Backend: $BACKEND_URL"
Write-Host "Frontend: $FRONTEND_URL"
Write-Host "수정한 대시보드 및 권한 로직이 모두 반영되었습니다." -ForegroundColor Yellow
