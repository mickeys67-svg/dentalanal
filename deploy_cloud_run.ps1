# deploy_cloud_run.ps1
# Automated Cloud Run Deployment Script

$ErrorActionPreference = "Stop"

function Read-Input-Default {
    param(
        [string]$Prompt,
        [string]$Default
    )
    $InputVal = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($InputVal)) {
        return $Default
    }
    return $InputVal
}

Write-Host "=== Google Cloud Run Deployment Setup ===" -ForegroundColor Cyan

# 1. Configuration
$PROJECT_ID = Read-Input-Default -Prompt "Enter Google Cloud Project ID" -Default "dentalanal-864421937037"
$REGION = Read-Input-Default -Prompt "Enter Cloud Run Region" -Default "us-west1"

# 2. Set Project
Write-Host "`nSetting active project to $PROJECT_ID..." -ForegroundColor Yellow
try {
    gcloud config set project $PROJECT_ID
} catch {
    Write-Error "Failed to set project. Please ensure you are logged in via 'gcloud auth login'."
    exit 1
}

# 3. Environment Variables (Backend)
Write-Host "`n=== Backend Configuration ===" -ForegroundColor Cyan
$BACKEND_SERVICE = Read-Input-Default -Prompt "Backend Service Name" -Default "d-mind-backend"
$DATABASE_URL = Read-Host "Enter DATABASE_URL (PostgreSQL connection string)"
$REDIS_URL = Read-Host "Enter REDIS_URL (Redis connection string)"
$GOOGLE_API_KEY = Read-Host "Enter GOOGLE_API_KEY (Gemini API Key)"

if (-not $DATABASE_URL -or -not $REDIS_URL -or -not $GOOGLE_API_KEY) {
    Write-Warning "Missing environment variables. Deployment might fail or service might not work correctly."
    $Proceed = Read-Host "Continue anyway? (y/n)"
    if ($Proceed -ne 'y') { exit }
}

# 4. Deploy Backend
Write-Host "`n=== Deploying Backend ($BACKEND_SERVICE) ===" -ForegroundColor Cyan
# Build and Deploy in one step using 'gcloud run deploy --source'
# Note: Using --source . uploads source and builds using Cloud Build automatically
Push-Location backend
gcloud run deploy $BACKEND_SERVICE `
    --source . `
    --region $REGION `
    --allow-unauthenticated `
    --set-env-vars "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,GOOGLE_API_KEY=$GOOGLE_API_KEY" `
    --port 8080 `
    --memory 4Gi
Pop-Location

# 5. Deploy Frontend
Write-Host "`n=== Frontend Configuration ===" -ForegroundColor Cyan
$DeployFrontend = Read-Host "Do you want to deploy the Frontend now? (y/n)"
if ($DeployFrontend -eq 'y') {
    $FRONTEND_SERVICE = Read-Input-Default -Prompt "Frontend Service Name" -Default "dentalanal" # Using the original name if likely
    
    # Check if we should use the Next.js Dockerfile
    # Gcloud run deploy source . uses buildpacks by default which might not work perfectly for complex Next.js
    # But let's try standard buildpack first or Dockerfile if present
    
    Write-Host "`n=== Deploying Frontend ($FRONTEND_SERVICE) ===" -ForegroundColor Cyan
    Push-Location frontend
    gcloud run deploy $FRONTEND_SERVICE `
        --source . `
        --region $REGION `
        --allow-unauthenticated `
        --memory 1Gi
    Pop-Location
}

Write-Host "`n=== Deployment Completed ===" -ForegroundColor Green
