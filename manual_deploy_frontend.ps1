# manual_deploy_frontend.ps1
# 프론트엔드 배포 스크립트

# 1. 백엔드 주소 (방금 배포된 주소)
$BACKEND_URL = "https://dentalanal-864421937037.us-west1.run.app"

# ---------------------------------------------------------
# 아래는 수정하지 않아도 됩니다. (자동 설정됨)
# ---------------------------------------------------------
$PROJECT_ID = "dentalanal"
$REGION = "us-west1"
$SERVICE_NAME = "dentalanal-frontend"

Write-Host "Deploying Frontend with Backend URL: $BACKEND_URL" -ForegroundColor Cyan

gcloud config set project $PROJECT_ID

# 1. Image Build (Explicitly using Dockerfile in ./frontend)
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"
Write-Host "Building Container Image: $IMAGE_NAME" -ForegroundColor Yellow

# Use --config if using cloudbuild.yaml, or just SOURCE for Dockerfile
# We will use the simple form but ensure we are in the right directory context
Push-Location frontend
gcloud builds submit . --tag $IMAGE_NAME
Pop-Location

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build Failed! Stopping deployment."
    exit 1
}

# 2. Deploy Service using the built image
Write-Host "Deploying Service..." -ForegroundColor Yellow

gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --region $REGION `
    --allow-unauthenticated `
    --port 3000 `
    --memory 1Gi `
    --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL"
