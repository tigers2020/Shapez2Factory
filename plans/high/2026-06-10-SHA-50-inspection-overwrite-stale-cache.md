---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: High
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Fix stale replay cache after inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` reuses the existing `SolverRun` row but only deletes `ReplayFrame` rows. It does not reset `status`, `algorithm_label`, `config_json`, denormalized fast-cache columns, or lifecycle pointers. Lab loaders can serve prior solver output after map overwrite rebuild.

## Scope

Reset `SolverRun` ORM fields and fast-cache mirrors when `overwrite=True` reuses an existing row, preventing stale composed replay from being served.

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38)
- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`

## Implementation Plan

1. In `experiment_service.resolve_inspection_solver_run` overwrite branch, after frame delete: set `run.status = PENDING`.
2. Clear artifact/lifecycle timestamps and fast-cache columns via `empty_solver_run_fast_cache_kwargs()`.
3. Assign `algorithm_label` and `config_json`; call `sync_solver_run_fast_cache_from_config_json` after reset.
4. `save()` before replay pipeline re-records frames.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (caller context)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: `python manage.py check`
- manual verification: seed completed run with stale cache → overwrite → cache empty

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-37/SHA-38 cache validity paths remain separate fixes.
