# PR pre-check — full pytest suite (parallel)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest -n auto --dist loadscope -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
