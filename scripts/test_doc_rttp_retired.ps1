# G4 — RTTP doc retirement standing gate (canon authority surfaces only).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
python -m pytest tests/unit/architecture/test_doc_rttp_retired_gates.py -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$canon = @(
    "documents/ai/current_plan.md",
    "documents/ai/START_HERE.md",
    "documents/index/document_inventory.md",
    "documents/Algorithm/README.md",
    "documents/Algorithm/asteroid_lab_00_overview.md",
    "documents/Algorithm/asteroid_lab_09_replay_timeline.md",
    "documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md",
    "documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md"
)
$hits = rg "RTTP Hybrid C" @canon --glob "!documents/archive/**" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Error "RTTP Hybrid C still on canon authority files:`n$hits"
}
exit 0
