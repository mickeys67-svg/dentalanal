# manual_deploy.ps1
# 이 파일에서 비밀번호만 수정하고 저장한 뒤 실행하세요.

# 1. 여기에 데이터베이스 비밀번호를 입력하세요 (따옴표 안에)
$DB_PASSWORD = "YOUR_DB_PASSWORD" 

# ---------------------------------------------------------
# 아래는 수정하지 않아도 됩니다. (자동 설정됨)
# ---------------------------------------------------------
$PROJECT_ID = "dentalanal"
$REGION = "us-west1"
$SERVICE_NAME = "dentalanal"

# API Key와 Redis URL은 이미 확인된 정보를 사용합니다.
$GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
$REDIS_URL = "YOUR_REDIS_URL"
$DATABASE_URL = "postgresql://postgres:$($DB_PASSWORD)@db.ugimcxylvgnmaiavylwf.supabase.co:5432/postgres"

Write-Host "Deploying with the following configuration:" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "Database: postgresql://postgres:***@db..."

gcloud config set project $PROJECT_ID

# Deploy Backend
gcloud run deploy $SERVICE_NAME `
    --source ./backend `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --memory 4Gi `
    --set-env-vars "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,GOOGLE_API_KEY=$GOOGLE_API_KEY"
