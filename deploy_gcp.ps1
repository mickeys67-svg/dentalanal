# Google Cloud Platform (GCP) Deployment Script for dentalanal
# Usage: powershell -ExecutionPolicy Bypass -File deploy_gcp.ps1

$PROJECT_ID = "dentalanal"
$REGION = "us-west1" # US West (Oregon) region
$REPO_NAME = "dentalanal-repo"

Write-Host "--- 1. Enabling Google Cloud APIs ---" -ForegroundColor Green
gcloud services enable run.googleapis.com sqladmin.googleapis.com redis.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project $PROJECT_ID

Write-Host "--- 2. Creating Artifact Registry Repository ---" -ForegroundColor Green
gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION --project $PROJECT_ID

# 3. Build and Push Backend
Write-Host "--- 3. Building Backend Image ---" -ForegroundColor Green
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend ./backend --project $PROJECT_ID

# 4. Build and Push Frontend
Write-Host "--- 4. Building Frontend Image ---" -ForegroundColor Green
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend ./frontend --project $PROJECT_ID

# 5. Cloud SQL & Memorystore (Redis) Setup
# NOTE: These take time. You may prefer to create them manually in the console.
Write-Host "--- 5. Deployment Note ---" -ForegroundColor Yellow
Write-Host "Cloud SQL 및 Memorystore 생성은 시간이 오래 걸릴 수 있습니다."
Write-Host "수동으로 생성한 후 연결 문자열(DATABASE_URL, REDIS_URL)을 환경 변수로 설정하는 것을 권장합니다."

# 6. Deploy Backend to Cloud Run
Write-Host "--- 6. Deploying Backend to Cloud Run ---" -ForegroundColor Green
gcloud run deploy dentalanal-backend `
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/backend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --cpu 1 `
    --memory 1Gi `
    --timeout 300 `
    --project $PROJECT_ID

# 7. Deploy Frontend to Cloud Run
Write-Host "--- 7. Deploying Frontend to Cloud Run ---" -ForegroundColor Green
$BACKEND_URL = (gcloud run services describe dentalanal-backend --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID)

gcloud run deploy dentalanal-frontend `
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/frontend `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL `
    --project $PROJECT_ID

Write-Host "--- Deployment Complete! ---" -ForegroundColor Cyan
Write-Host "Frontend URL: " -NoNewline
gcloud run services describe dentalanal-frontend --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID
