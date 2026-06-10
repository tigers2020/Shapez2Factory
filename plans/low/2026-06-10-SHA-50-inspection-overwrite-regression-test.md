---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Low
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Inspection overwrite fast-cache regression test

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test covers fast-cache column reset when `resolve_inspection_solver_run(..., overwrite=True)` follows a mocked completed solver state.

## Scope

Extend `test_experiment_service.py` (or replay pipeline test) with regression asserting stale cache cleared after overwrite.

## Non-goals

- Production behavior change beyond test coverage

## Implementation Plan

1. Seed `SolverRun` with `status=completed`, populated `solver_summary_json` and `lab_replay_payload_json`.
2. Call `resolve_inspection_solver_run(..., overwrite=True)`.
3. Assert fast-cache columns empty and status reset to inspection scaffolding.
4. Extend `test_build_initial_replay_overwrite_keeps_run_key` if appropriate.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py` (optional)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -k overwrite -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Should ship in same PR as High/Mid fix for regression gate.
