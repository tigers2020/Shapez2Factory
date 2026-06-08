# Agent governance acceptance checks. Exit 1 on failure.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$failed = $false

function Test-LineLimit {
    param([string]$Path, [int]$Max = 75)
    $lines = (Get-Content -LiteralPath $Path).Count
    if ($lines -gt $Max) {
        Write-Host "FAIL line limit: $Path has $lines lines (max $Max)"
        $script:failed = $true
    } else {
        Write-Host "OK   line limit: $Path ($lines)"
    }
}

Test-LineLimit (Join-Path $root "AGENTS.md")
Get-ChildItem -Path (Join-Path $root ".cursor\rules") -Filter "*.mdc" | ForEach-Object {
    Test-LineLimit $_.FullName
}

$rootMdc = Get-Content -LiteralPath (Join-Path $root ".cursor\rules\root.mdc") -Raw
foreach ($needle in @("00-hermes-skill-suggestion.mdc", "01-hermes-handoff-format.mdc", "docs/agent-workflows/")) {
    if ($rootMdc -notmatch [regex]::Escape($needle)) {
        Write-Host "FAIL root.mdc missing route: $needle"
        $failed = $true
    }
}
if (-not $failed) { Write-Host "OK   root.mdc Hermes routes" }

$agentScope = Get-Content -LiteralPath (Join-Path $root ".cursor\rules\agent_scope.mdc") -Raw
if ($agentScope -notmatch "Hermes handoff exception") {
    Write-Host "FAIL agent_scope.mdc missing Hermes handoff exception"
    $failed = $true
} else {
    Write-Host "OK   agent_scope Hermes exception"
}

$handoff = Get-Content -LiteralPath (Join-Path $root "docs\agent-workflows\hermes-handoff.md") -Raw
foreach ($marker in @("PLAN_TO_SKILL_REQUEST", "SKILL_SUGGESTION", "SKILL_APPLICATION_SUMMARY", "AGENTS.md")) {
    if ($handoff -notmatch [regex]::Escape($marker)) {
        Write-Host "FAIL hermes-handoff.md missing: $marker"
        $failed = $true
    }
}
if (-not $failed) { Write-Host "OK   hermes-handoff markers" }

$agents = Get-Content -LiteralPath (Join-Path $root "AGENTS.md") -Raw
foreach ($cmd in @("python manage.py check", "mypy django_apps config src", "scripts/test_fast.ps1")) {
    if ($agents -notmatch [regex]::Escape($cmd)) {
        Write-Host "FAIL AGENTS.md missing validation: $cmd"
        $failed = $true
    }
}
if (-not $failed) { Write-Host "OK   AGENTS.md validation commands" }

if ($failed) {
    Write-Host "`nGovernance check FAILED"
    exit 1
}
Write-Host "`nGovernance check PASSED"
exit 0
