---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: High
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Stack-failure manifest error_code and Django ingest FAILED indexing

## Source Issue

- Linear: SHA-33
- Status at planning time: In Progress (moved from Todo after prior automation pass)
- Priority: High

## Problem

When the L2–L6 stack fails (`failed_layer_slug` set, CLI exit `STACK_UNAVAILABLE` / 20), the CLI still finalizes an artifact whose `manifest.error_code` is always `null`. Django `ingest_artifact_for_project` treats a null `error_code` as success and writes `SolverRun.status=COMPLETED` / `lifecycle_status=succeeded`, even though `solver_summary.json` records `run_success: false` and the subprocess exited non-zero.

## Scope

- Populate `manifest.error_code` when `RunStackUseCase` reports stack failure (`ok=False`).
- Harden `ingest_artifact_for_project` so stack-failure artifacts index as FAILED even if manifest `error_code` were null (defense in depth via `solver_summary.run_success`).
- Add regression tests for exit-20 artifact ingest path.

## Non-goals

- Changing CLI `ExitCode` enum values (keep `STACK_UNAVAILABLE = 20`).
- Altering successful artifact schema or hash rules.
- Fixing sync subprocess ingest skip (SHA-45 — separate mid plan).

## Implementation Plan

1. **Audit current failure propagation**
   - `src/shapez2_factory/application/asteroid_lab/run_stack.py`: `StackRunResult.error_code` is always `None` (line ~234) despite `ok=False` when `failed_layer_slug` is set.
   - `src/shapez2_factory/interfaces/cli/asteroid_solve.py`: manifest gets `error_code=result.error_code` (line ~283).
   - `django_apps/asteroid_lab/services/artifact_ingest.py`: status derived only from `manifest.error_code` truthiness (lines ~169–186).

2. **Set CLI/application error_code on stack failure**
   - In `RunStackUseCase.run`, when `failed_layer_slug` is not `None`, set `error_code` to a stable string constant (e.g. `"stack_unavailable"` aligned with `ExitCode.STACK_UNAVAILABLE` name; document choice in code comment).
   - Optionally include `failed_layer_slug` in `solver_summary` (already present) — do not duplicate into manifest beyond `error_code`.

3. **Harden Django ingest status selection**
   - In `ingest_artifact_for_project`, compute run failure from:
     - `manifest.error_code` is truthy, **or**
     - `solver_summary.get("run_success") is False`
   - Map failure → `SolverRun.RunStatus.FAILED` / `lifecycle_status="failed"`.
   - Preserve warm-cache skip for non-COMPLETED (existing behavior).

4. **CLI regression test (exit 20 + manifest error_code)**
   - Extend or add test in `tests/unit/shapez2_factory/test_cli_run_artifact.py` or `test_cli_exit_codes.py`:
     - Force stack failure (e.g. zero budget, invalid layer input fixture, or mock `RunStackUseCase` returning `ok=False`).
     - Assert CLI returns `ExitCode.STACK_UNAVAILABLE` (20).
     - Assert finalized `manifest.json` has non-null `error_code`.
     - Assert `solver_summary.json` has `run_success: false`.

5. **Django ingest regression test**
   - Add test in `tests/unit/asteroid_lab/test_artifact_ingest.py`:
     - Fixture artifact with `error_code: "stack_unavailable"`, valid hashes, `run_success: false` in summary.
     - Assert `SolverRun.status == FAILED`, `lifecycle_status == "failed"`.
   - Add defense-in-depth test: `error_code: null` but `run_success: false` → still FAILED.

6. **Run validation gates**
   - `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/asteroid_lab/test_artifact_ingest.py -v`
   - `ruff check src/shapez2_factory/application/asteroid_lab/run_stack.py django_apps/asteroid_lab/services/artifact_ingest.py`

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only if error_code flows from use case)
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py` or `tests/unit/shapez2_factory/test_cli_exit_codes.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/ django_apps/asteroid_lab/services/artifact_ingest.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py tests/unit/asteroid_lab/test_artifact_ingest.py -v`
- build: N/A
- manual verification: Run CLI with fixture that fails mid-stack; ingest artifact dir; confirm FAILED SolverRun in admin/DB

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Manifest `error_code` string must align with future `SolverRuntimeEntryErrorCode` additions (SHA-7 exit-code table drift). Prefer a named constant shared across CLI manifest and Django ingest docs.
- `run_success: false` defense-in-depth may mark FAILED for artifacts that intentionally carry partial diagnostics with null `error_code` — confirm no legitimate success path sets `run_success: false`.
- Pair implementation order with SHA-45: ingest hardening helps async path immediately; sync path still skips ingest until SHA-45 lands.
