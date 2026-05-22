# Daily TDD — fast unit slice (see documents/ai/manuals/testing.md)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest -m "unit and not slow" -n auto --dist loadscope -q @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
