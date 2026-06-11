---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Apply algorithm_label and config on inspection overwrite

## Source Issue

- Linear: SHA-50
- Priority: Mid

## Problem

Overwrite branch ignores `algorithm_label` and `config` arguments passed to `resolve_inspection_solver_run`.

## Scope

Apply passed args when reusing row on overwrite, mirroring `create_solver_run`.

## Implementation Plan

1. In overwrite branch, assign `run.algorithm_label` and `run.config_json` from function args.
2. Call `sync_solver_run_fast_cache_from_config_json(run)` after reset.
3. Extend `test_build_initial_replay_overwrite_keeps_run_key` to assert label/config applied.
4. Run `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- tests: experiment + replay pipeline unit tests

## Acceptance Criteria

- [ ] `algorithm_label` and `config` applied on overwrite.

## Risks / Open Questions

- May ship in same PR as high plan.
