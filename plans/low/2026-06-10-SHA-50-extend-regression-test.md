---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Low
labels:
  - bug
  - test
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Extend regression test for fast-cache column reset on overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test covers fast-cache reset when `resolve_inspection_solver_run(..., overwrite=True)` reuses a row previously warmed by solver execution. `test_build_initial_replay_overwrite_keeps_run_key` asserts run key stability but not that stale `solver_summary_json` / `lab_replay_payload_json` columns are cleared.

## Scope

Extend regression test in `test_experiment_service.py` (or replay pipeline test) asserting seeded completed state with populated fast-cache → overwrite → empty cache columns and inspection scaffolding status.

## Non-goals

- Changing overwrite semantics beyond test coverage.
- Full matrix of all fast-cache column combinations.
- Integration test through Lab UI.

## Implementation Plan

1. Review `tests/unit/asteroid_lab/test_experiment_service.py` and `test_replay_pipeline_service.py` for overwrite fixtures.
2. Extend `test_build_initial_replay_overwrite_keeps_run_key` (or add sibling test):
   - Seed `SolverRun` with `status=completed`, `solver_summary_json={"stale": true}`, non-empty `lab_replay_payload_json` and `lab_replay_manifest_summary_json`.
   - Call `resolve_inspection_solver_run(..., overwrite=True)`.
   - Assert `run_key` unchanged (existing contract).
   - Assert fast-cache columns empty / reset per `empty_solver_run_fast_cache_kwargs()`.
   - Assert `status` is inspection scaffolding (e.g. `PENDING`), not `COMPLETED`.
3. Assert `algorithm_label` and `config_json` from overwrite args applied.
4. Run: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py` (optional sibling test)
- `django_apps/asteroid_lab/services/experiment_service.py` (subject under test)
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py` (expected empty values reference)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_experiment_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test fails on pre-fix overwrite behavior (stale cache retained).
- [ ] Test asserts fast-cache columns cleared after overwrite.
- [ ] Test asserts status reset and config/algorithm applied.
- [ ] No-overwrite idempotent path still covered and unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Test must seed realistic column JSON shapes so loader paths would have served stale data pre-fix.
- Depends on Mid scope implementation landing first for green test.
