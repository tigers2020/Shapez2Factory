# Merge .devtool/kanban.settings.json into .vscode/settings.json (workspace-local).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path (Join-Path $root ".devtool") "kanban.settings.json"
$targetDir = Join-Path $root ".vscode"
$target = Join-Path $targetDir "settings.json"

if (-not (Test-Path $source)) {
    Write-Error "Missing $source"
}

$kanban = Get-Content $source -Raw | ConvertFrom-Json
$merged = @{}

if (Test-Path $target) {
    $existing = Get-Content $target -Raw | ConvertFrom-Json
    if ($null -ne $existing) {
        foreach ($prop in $existing.PSObject.Properties) {
            $merged[$prop.Name] = $prop.Value
        }
    }
}

foreach ($prop in $kanban.PSObject.Properties) {
    $merged[$prop.Name] = $prop.Value
}

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
}

($merged | ConvertTo-Json -Depth 10) + "`n" | Set-Content -Path $target -Encoding utf8
Write-Host "Merged kanban-markdown settings into $target"
