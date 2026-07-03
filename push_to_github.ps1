Write-Host "--- Git Push to GitHub ---" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# 1. Stage all changes
Write-Host "[1/3] Staging all changes..." -ForegroundColor Yellow
git add -A

# 2. Commit
$msg = "feat: modern UI/UX redesign - dark sidebar, indigo accent, split auth pages"
Write-Host "[2/3] Committing: $msg" -ForegroundColor Yellow
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m $msg
    Write-Host "Committed successfully." -ForegroundColor Green
} else {
    Write-Host "Nothing new to commit - pushing existing commits." -ForegroundColor Gray
}

# 3. Push
Write-Host "[3/3] Pushing to origin/main..." -ForegroundColor Yellow
git push origin main

Write-Host "`n[Done] Successfully pushed to GitHub!" -ForegroundColor Green
Write-Host "Repository: https://github.com/mickeys67-svg/dentalanal" -ForegroundColor Cyan
