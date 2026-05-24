# Reconstruction replay / topology / island_bbox narrow gate (no RTTP, no macro).
# See documents/ai/current_plan.md § Reconstruction narrow gate.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$pytestPaths = @(
    "tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py",
    "tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py",
    "tests/unit/asteroid_lab/test_reconstruction_replay_merge.py",
    "tests/unit/asteroid_lab/test_island_bbox.py",
    "tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py",
    "tests/unit/asteroid_lab/test_replay_snapshot_contract.py",
    "tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py"
)

python -m pytest @pytestPaths -v --tb=short @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m ruff check `
    django_apps/asteroid_lab/reconstruction `
    django_apps/asteroid_lab/replay `
    django_apps/asteroid_lab/snapshots/island_bbox.py `
    django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
