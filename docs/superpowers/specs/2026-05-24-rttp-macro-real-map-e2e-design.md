# RTTP macro real-map E2E (fixture)

**Status:** implemented  
**Date:** 2026-05-24

## Goal

Prove **macro-only** RTTP through the same runtime path as Lab/CLI (reconstruction → adapter → pipeline → persisted `solver_summary`) using a **real** copy-code map, without `optimization_input` monkeypatch.

## Fixture

- Path: `tests/fixtures/asteroid_lab/macro_e2e_copy.code`
- Source: OPS-verified project class (`copy-import-495e552c` export, 2026-05-24)
- Single SHAPEZ2 line; slug is **not** pinned in tests

## Test contract

File: `tests/integration/asteroid_lab/test_rttp_macro_real_map_e2e.py`

- `run_solver_runtime_for_project` with `macro_only_mode=true`, `rttp_record_replay=false`
- Assert: `validation_passed`, `macro_commit_summary` scalars (1 macro, 3 children, `domain_version` set, `conflict_count==0`)
- Assert: `run_summary` and persisted `solver_summary` include same HUD payload
- **Forbidden:** using replay/metrics as solver input (read-only asserts only)

## CI

Included in `.github/workflows/rttp-lab-macro-smoke.yml`.

## Non-goals

- Browser/HTTP E2E
- Golden hash slot ids
- Algorithm or validation policy changes
- Replay lazy-load (13C)
