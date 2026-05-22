# Slow contracts — game_data import, exhaustive genes, heavy modules
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest -m slow -n auto --dist loadscope -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
