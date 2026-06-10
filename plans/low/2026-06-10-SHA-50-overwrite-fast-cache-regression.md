---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Low
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for fast-cache reset on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test covers fast-cache column reset when `resolve_inspection_solver_run(..., overwrite=True)` reuses a row that previously held completed solver state with warm-cache columns populated.

## Scope

Extend `test_experiment_service.py` (or replay pipeline test) with regression: seed completed `SolverRun` with stale fast-cache → overwrite → assert columns empty and status reset.

## Non-goals

- Changing no-overwrite idempotent path behavior tests unless regression requires.

## Implementation Plan

1. Open `tests/unit/asteroid_lab/test_experiment_service.py`.
2. Add `test_resolve_inspection_overwrite_clears_stale_fast_cache`:
   - Create inspection `SolverRun` with `status=COMPLETED`, `solver_summary_json={"stale": true}`, non-empty `lab_replay_payload_json`.
   - Call `resolve_inspection_solver_run(..., overwrite=True)`.
   - Assert `status == PENDING` (or inspection scaffolding).
   - Assert fast-cache columns match `empty_solver_run_fast_cache_kwargs()` defaults.
   - Assert `algorithm_label` / `config_json` from call args applied.
3. Optionally extend `test_build_initial_replay_overwrite_keeps_run_key` in `test_replay_pipeline_service.py`.
4. Run: `pytest tests/unit/asteroid_lab/test_experiment_service.py::test_resolve_inspection_overwrite_clears_stale_fast_cache -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py` (optional)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_experiment_service.py`
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v -k overwrite`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test covers seeded completed state → overwrite → empty cache.
- [ ] Matches the source issue spec.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Test must run after Mid/High implementation lands or use xfail until then.
