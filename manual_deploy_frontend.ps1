# manual_deploy_frontend.ps1
# 프론트엔드 배포 스크립트

# 1. 백엔드 주소 (방금 배포된 주소)
$BACKEND_URL = "https://dentalanal-864421937037.us-west1.run.app"

# ---------------------------------------------------------
# 아래는 수정하지 않아도 됩니다. (자동 설정됨)
# ---------------------------------------------------------
$PROJECT_ID = "dentalanal"
$REGION = "us-west1"
$SERVICE_NAME = "dentalanal"

Write-Host "Deploying Frontend with Backend URL: $BACKEND_URL" -ForegroundColor Cyan

gcloud config set project $PROJECT_ID

# 1. Image Build (Using cloudbuild.yaml for proper env injection)
Write-Host "Building Container Image with Backend URL: $BACKEND_URL" -ForegroundColor Yellow

$SUBSTITUTIONS = "_API_URL=$BACKEND_URL,_REGION=$REGION,_PROJECT_ID=$PROJECT_ID,_REPO_NAME=dentalanal-repo"

gcloud builds submit . `
    --config ./frontend/cloudbuild.yaml `
    --substitutions $SUBSTITUTIONS `
    --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build Failed! Stopping deployment."
    exit 1
}

$IMAGE_NAME = "$REGION-docker.pkg.dev/$PROJECT_ID/dentalanal-repo/frontend:latest"

# 2. Deploy Service using the built image
Write-Host "Deploying Service: $SERVICE_NAME" -ForegroundColor Yellow

gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --region $REGION `
    --allow-unauthenticated `
    --port 3000 `
    --memory 1Gi `
    --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL" `
    --project $PROJECT_ID
