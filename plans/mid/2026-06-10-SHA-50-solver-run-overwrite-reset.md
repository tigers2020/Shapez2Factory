---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Mid
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Reset ORM lifecycle and apply config on SolverRun overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Mid

## Problem

The overwrite branch ignores `algorithm_label` and `config` arguments and does not reset ORM lifecycle fields. Reused rows retain stale metadata from prior solver runs.

## Scope

Reset ORM lifecycle fields and fast-cache mirrors when `overwrite=True` reuses an existing row; apply `algorithm_label` and `config` (and `sync_solver_run_fast_cache_from_config_json`) on overwrite.

## Non-goals

- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`.
- Changing `create_solver_run` row-creation path.

## Implementation Plan

1. Read `create_solver_run` in `experiment_service.py` for the canonical field initialization pattern.
2. In overwrite branch after frame delete: assign `algorithm_label` and `config_json` from call args.
3. Call `sync_solver_run_fast_cache_from_config_json` after reset (or apply `empty_solver_run_fast_cache_kwargs()` then sync).
4. Mirror `create_solver_run` field defaults minus row creation.
5. `save()` the row before returning DTO.
6. Verify `build_initial_replay_for_map_input` overwrite path receives correctly reset row.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Must confirm which `status` value matches inspection scaffolding vs completed solver; align with existing `create_solver_run` convention.
