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

# Plan: Regression test for fast-cache column reset on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: In Progress (moved from Todo by backlog automation)
- Priority: Low

## Problem

No unit test covers fast-cache column reset when `resolve_inspection_solver_run(..., overwrite=True)` reuses a row previously indexed by solver execution. Existing `test_build_initial_replay_overwrite_keeps_run_key` only asserts run_key/id stability, not cache clearing.

## Scope

Add regression test(s) asserting stale fast-cache columns and COMPLETED status are cleared after overwrite.

## Non-goals

- Implementing the fix (covered by High/Mid plans).
- Testing SHA-37/SHA-38 read-path validity rules.

## Implementation Plan

1. Extend `tests/unit/asteroid_lab/test_experiment_service.py` with `test_resolve_inspection_solver_run_overwrite_clears_fast_cache`:
   - Create project + `SolverRun` with `status=COMPLETED`, `solver_summary_json={"stale": true}`, non-empty `lab_replay_payload_json` (composed frames), populated `lab_replay_manifest_summary_json`, non-empty `solver_runtime_replay_frames_json`.
   - Call `resolve_inspection_solver_run(project_id, run_key=..., algorithm_label="inspection", config={}, overwrite=True)`.
   - Refresh ORM row; assert `status == PENDING`, all four fast-cache columns match `empty_solver_run_fast_cache_kwargs()` expectations (use patterns from `test_solver_run_fast_cache.py`).
2. Extend `test_build_initial_replay_overwrite_keeps_run_key` in `tests/unit/asteroid_lab/test_replay_pipeline_service.py`:
   - After first `build_initial_replay_for_map_input`, manually seed `SolverRun` fast-cache + `COMPLETED` status.
   - Call overwrite rebuild; assert fast-cache columns empty and status pending before/at end of pipeline (depending on whether pipeline re-populates manifest during same call — document expected post-overwrite state per contract).
3. Run targeted pytest; ensure test fails on current main (red) before fix lands, or mark xfail only if implementing test after fix in same PR.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_solver_run_fast_cache.py` (reference patterns only)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v -k overwrite`
- typecheck: N/A (test-only)
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test covers seeded completed state → overwrite → empty cache.
- [ ] Test asserts `algorithm_label` / `config` applied when passed.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Pipeline-level test may re-populate some manifest fields during the same call; scope assertions to post-`resolve_inspection_solver_run` ORM state or use direct service call to isolate overwrite contract.
