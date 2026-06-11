# Agent governance acceptance checks.

# WARN (root AGENTS.md above soft target): exit 0. FAIL (hard max / other checks): exit 1.

$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent

$failed = $false

$warned = $false



function Test-LineLimit {

    param(

        [string]$Path,

        [int]$Max,

        [int]$Target = 0

    )

    $lines = (Get-Content -LiteralPath $Path).Count

    if ($lines -gt $Max) {

        Write-Host "FAIL line limit: $Path has $lines lines (max $Max)"

        $script:failed = $true

    } elseif ($Target -gt 0 -and $lines -gt $Target) {

        Write-Host "WARN line target: $Path has $lines lines (target $Target, max $Max) — exit 0, no action required"

        $script:warned = $true

    } else {

        Write-Host "OK   line limit: $Path ($lines)"

    }

}



$rootAgents = Join-Path $root "AGENTS.md"

Test-LineLimit -Path $rootAgents -Max 120 -Target 75



Get-ChildItem -Path $root -Filter "AGENTS.md" -Recurse -File |

    Where-Object { $_.FullName -ne $rootAgents } |

    ForEach-Object {

        Test-LineLimit -Path $_.FullName -Max 150

    }



Get-ChildItem -Path (Join-Path $root ".cursor\rules") -Filter "*.mdc" | ForEach-Object {

    Test-LineLimit -Path $_.FullName -Max 75

}



$rootMdc = Get-Content -LiteralPath (Join-Path $root ".cursor\rules\root.mdc") -Raw

foreach ($needle in @("workflow.mdc", "agent_scope.mdc")) {

    if ($rootMdc -notmatch [regex]::Escape($needle)) {

        Write-Host "FAIL root.mdc missing route: $needle"

        $failed = $true

    }

}

if (-not $failed) { Write-Host "OK   root.mdc core routes" }



$agents = Get-Content -LiteralPath $rootAgents -Raw

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

if ($warned) {

    Write-Host "`nGovernance check PASSED (with warnings; do not edit solely to clear WARN)"

} else {

    Write-Host "`nGovernance check PASSED"

}

exit 0

