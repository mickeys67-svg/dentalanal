# GCP Deployment Script (dentalanal) - SECURE VERSION
# Usage: .\deploy.ps1
# This script will build and deploy both backend and frontend to Google Cloud Run.

$PROJECT_ID = "dentalanal"
$REGION = "us-west1"
$REPO_NAME = "dentalanal-repo"

Write-Host "--- 1. GCP 환경 설정 및 API 활성화 ---" -ForegroundColor Green
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

# Artifact Registry 확인 및 생성
$repoExists = gcloud artifacts repositories list --location=$REGION --filter="name:projects/$PROJECT_ID/locations/$REGION/repositories/$REPO_NAME" --format="value(name)" --project $PROJECT_ID
if (-not $repoExists) {
    Write-Host "--- 2. Artifact Registry 생성 ---" -ForegroundColor Green
    gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --project $PROJECT_ID
}

Write-Host "--- 3. 백엔드(Backend) 이미지 빌드 및 배포 ---" -ForegroundColor Green
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend ./backend --project $PROJECT_ID

# [SECURE] 기밀 정보는 이 파일에 하드코딩하지 마십시오.
# 윈도우 환경 $env: 변수나 비밀 저장소를 사용하세요.
$DB_PWD = $env:DATABASE_PASSWORD # 👈 환경변수 세팅 필요
$DB_ID = "uujxtnvpqdwcjqhsoshi"
$DB_HOST = "db.$($DB_ID).supabase.co"
$DB_URL = "postgresql://postgres:$($DB_PWD)@$($DB_HOST):5432/postgres?sslmode=require"

gcloud run deploy dentalanal-backend `
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 1Gi `
    --timeout 300 `
    --set-env-vars "DATABASE_URL=$DB_URL,DATABASE_PASSWORD=$DB_PWD" `
    --project $PROJECT_ID

# 배포된 백엔드 URL 획득
$BACKEND_URL = (gcloud run services describe dentalanal-backend --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID).Trim()
if ([string]::IsNullOrWhiteSpace($BACKEND_URL)) {
    Write-Error "--- 에러: 백엔드 URL을 찾을 수 없습니다. ---"
    exit 1
}
Write-Host "Detected Backend URL: $BACKEND_URL" -ForegroundColor Cyan

Write-Host "--- 4. 프런트엔드(Frontend) 이미지 빌드 및 배포 ---" -ForegroundColor Green
$SUBSTITUTIONS = "_API_URL=$BACKEND_URL,_REGION=$REGION,_PROJECT_ID=$PROJECT_ID,_REPO_NAME=$REPO_NAME"
gcloud builds submit . --config ./frontend/cloudbuild.yaml --substitutions $SUBSTITUTIONS --project $PROJECT_ID

gcloud run deploy dentalanal `
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend:latest `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL `
    --project $PROJECT_ID

$FRONTEND_URL = (gcloud run services describe dentalanal --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID).Trim()
Write-Host "`n--- 배포 완료! ---" -ForegroundColor Cyan
Write-Host "Backend: $BACKEND_URL"
Write-Host "Frontend: $FRONTEND_URL"
