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

# Plan: Regression test for fast-cache reset on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test covers fast-cache column reset when `resolve_inspection_solver_run(..., overwrite=True)` follows a mocked completed solver state.

## Scope

Extend `test_experiment_service.py` or `test_replay_pipeline_service.py` to assert stale cache cleared after overwrite.

## Non-goals

- Full integration test through Lab UI.
- Changing `create_or_replace_solver_run` tests.

## Implementation Plan

1. Seed `SolverRun` with `status=completed`, `solver_summary_json={"stale": true}`, and populated `lab_replay_payload_json`.
2. Call `resolve_inspection_solver_run(..., overwrite=True)`.
3. Assert fast-cache columns empty/null and `status` reset to inspection scaffolding (e.g. `PENDING`).
4. Extend `test_build_initial_replay_overwrite_keeps_run_key` if it already covers run_key stability.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: N/A
- manual verification: Test fails on current overwrite-retains-cache behavior

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Regression test covers seeded completed state → overwrite → empty cache.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Use existing fixtures from `test_solver_run_fast_cache.py` where possible.
