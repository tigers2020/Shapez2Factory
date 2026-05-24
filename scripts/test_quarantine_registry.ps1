# PR-D standing gate — quarantine registry (see documents/ai/current_plan.md).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pytest tests/unit/architecture/test_quarantined_paths_do_not_leak.py -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m ruff check tests/unit/architecture/quarantine_registry.py tests/unit/architecture/test_quarantined_paths_do_not_leak.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
