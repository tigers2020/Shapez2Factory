# PR-B standing gate — optimization import canon (see documents/ai/current_plan.md).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pytest tests/unit/architecture/test_optimization_contamination_gates.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m ruff check django_apps/asteroid_lab/optimization tests/unit/architecture
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
