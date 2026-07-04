# =============================================================================
# git-push.ps1 — GitHub push 헬퍼 (Credential Manager 대화상자 우회)
#
# 사용법:
#   1) .github_token 파일을 열어 PASTE_YOUR_GITHUB_PAT_HERE 를 실제 GitHub PAT로 교체
#      (토큰 발급: https://github.com/settings/tokens  → repo 권한)
#   2) PowerShell 에서:  .\git-push.ps1            (main 브랜치 push)
#                   또는  .\git-push.ps1 <브랜치명>
#
# .github_token 은 .gitignore 에 등록되어 커밋되지 않습니다. 토큰은 화면에 출력되지 않습니다.
# =============================================================================
$ErrorActionPreference = "Stop"

$repo   = "github.com/mickeys67-svg/dentalanal.git"
$branch = if ($args.Count -ge 1) { $args[0] } else { "main" }

$tokenFile = Join-Path $PSScriptRoot ".github_token"
if (-not (Test-Path $tokenFile)) {
    Write-Host "[오류] .github_token 파일이 없습니다. 이 폴더에 만들고 GitHub PAT를 넣으세요." -ForegroundColor Red
    exit 1
}

$token = (Get-Content $tokenFile -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($token) -or $token -eq "PASTE_YOUR_GITHUB_PAT_HERE") {
    Write-Host "[오류] .github_token 에 실제 GitHub PAT를 붙여넣으세요 (아직 자리표시자 상태)." -ForegroundColor Red
    exit 1
}

Write-Host "→ origin/$branch 로 push 중... (토큰은 출력하지 않음)" -ForegroundColor Cyan

# credential.helper 를 비워 GCM 대화상자를 우회하고, 토큰을 URL로 직접 전달.
# x-access-token 형식은 GitHub 권장 방식.
git -c credential.helper= push "https://x-access-token:$token@$repo" "$branch`:$branch"
$code = $LASTEXITCODE

if ($code -eq 0) {
    Write-Host "✅ push 성공: origin/$branch" -ForegroundColor Green
} else {
    Write-Host "❌ push 실패 (exit $code). 토큰 유효성/권한을 확인하세요." -ForegroundColor Red
}
exit $code
