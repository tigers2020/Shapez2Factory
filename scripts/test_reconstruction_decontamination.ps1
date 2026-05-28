$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest tests/unit/architecture/test_reconstruction_decontamination_gates.py -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
rg "run_rttp_pipeline" django_apps harness src -g "*.py"
if ($LASTEXITCODE -eq 0) { throw "run_rttp_pipeline still referenced in runtime code" }
exit 0
