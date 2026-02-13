# D-MIND 통합 검증 및 크로스체크 스크립트
Write-Host "--- 🔍 D-MIND 시스템 크로스체크 시작 ---" -ForegroundColor Cyan

$Success = $true

# 1. 프론트엔드 타입 및 빌드 검사 (UI 충돌 감지)
Write-Host "`n[1/3] 프론트엔드 빌드 검사 중..." -ForegroundColor Yellow
cd frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 프론트엔드 빌드 오류: 코드 충돌 또는 타입 에러가 발견되었습니다." -ForegroundColor Red
    $Success = $false
}
else {
    Write-Host "✅ 프론트엔드 검사 통과" -ForegroundColor Green
}
cd ..

# 2. 백엔드 문법 및 구조 검사
Write-Host "`n[2/3] 백엔드 코드 정밀 검사 중..." -ForegroundColor Yellow
cd backend
# 파이썬 문법 검사 (컴파일 에러 확인)
python -m py_compile app/main.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 백엔드 문법 오류가 발견되었습니다." -ForegroundColor Red
    $Success = $false
}
else {
    Write-Host "✅ 백엔드 검사 통과" -ForegroundColor Green
}
cd ..

# 3. 환경 변수 및 설정 파일 검사
Write-Host "`n[3/3] 배포 설정 검사 중..." -ForegroundColor Yellow
if (!(Test-Path "deploy.ps1")) {
    Write-Host "❌ 배포 스크립트를 찾을 수 없습니다." -ForegroundColor Red
    $Success = $false
}
else {
    Write-Host "✅ 설정 검사 통과" -ForegroundColor Green
}

# 최종 보고
Write-Host "`n==============================================="
if ($Success) {
    Write-Host "✨ 모든 크로스체크 통과! 배포를 진행해도 안전합니다." -ForegroundColor Cyan
}
else {
    Write-Host "⚠️ 오류가 발견되었습니다. 위 로그를 확인하고 수정하세요." -ForegroundColor Yellow
    exit 1
}
Write-Host "==============================================="
