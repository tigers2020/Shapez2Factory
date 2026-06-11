---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for overwrite fast-cache reset

## Source Issue

- Linear: SHA-50
- Priority: Low

## Problem

No unit test covers fast-cache column reset on overwrite after mocked completed solver state.

## Scope

Add/extend regression test only.

## Implementation Plan

1. In `test_experiment_service.py`, add `test_resolve_inspection_overwrite_clears_stale_fast_cache`.
2. Seed `SolverRun` with `status=completed`, `solver_summary_json={"stale": true}`, non-empty `lab_replay_payload_json`.
3. Call `resolve_inspection_solver_run(..., overwrite=True)`.
4. Assert fast-cache columns empty and status reset.
5. Run targeted pytest.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`

## Validation Plan

- tests: new regression test

## Acceptance Criteria

- [ ] Test fails on current code, passes after high/mid fix.

## Risks / Open Questions

- TDD: write test first per project convention.
