# Capacity C-GATE standing gate — complete-map SoT (see documents/ai/current_plan.md).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/services/reconstruction_capacity_summary.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
