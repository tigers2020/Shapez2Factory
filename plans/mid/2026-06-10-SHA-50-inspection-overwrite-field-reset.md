---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Mid
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Inspection overwrite lifecycle field reset

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Mid

## Problem

Overwrite path must apply `algorithm_label` and `config` on the reused row and mirror `create_solver_run` scaffolding semantics minus row creation.

## Scope

Ensure overwrite applies passed `algorithm_label` and `config` after lifecycle/cache reset, matching `create_solver_run` field assignment pattern.

## Non-goals

- Delete-and-recreate semantics change
- Replay pipeline idempotent short-circuit change

## Implementation Plan

1. Compare `create_solver_run` field assignment with overwrite branch in `experiment_service.py`.
2. Apply `algorithm_label`, `config_json`, and `sync_solver_run_fast_cache_from_config_json` on overwrite after reset.
3. Verify DTO returned reflects updated fields.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: N/A
- manual verification: overwrite with new config → row reflects new config

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlaps High plan — implement together in one PR if practical.
