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

# Plan: Regression test for SolverRun fast-cache reset on overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test covers fast-cache column reset when `resolve_inspection_solver_run(..., overwrite=True)` reuses a row that previously held completed solver state.

## Scope

Extend regression test asserting stale fast-cache columns are cleared after overwrite following a mocked completed solver state.

## Non-goals

- Full replay pipeline integration test.
- Testing every fast-cache column permutation.

## Implementation Plan

1. Read `test_build_initial_replay_overwrite_keeps_run_key` in `tests/unit/asteroid_lab/test_experiment_service.py`.
2. Extend or add test: seed `SolverRun` with `status=completed`, `solver_summary_json={"stale": true}`, populated `lab_replay_payload_json`.
3. Call `resolve_inspection_solver_run(..., overwrite=True)`.
4. Assert fast-cache columns empty/reset and status is inspection scaffolding.
5. Assert `run_key` unchanged (idempotent key retention).
6. Run `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py` (optional companion)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_experiment_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing first; test will fail until overwrite reset is implemented.
