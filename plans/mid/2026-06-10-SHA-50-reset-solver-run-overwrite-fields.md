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

# Plan: Reset ORM lifecycle fields and apply config on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: In Progress (moved from Todo by backlog automation)
- Priority: Mid

## Problem

The overwrite branch of `resolve_inspection_solver_run` ignores `algorithm_label` and `config` arguments and does not reset ORM lifecycle fields (`status`, `artifact_root`, `lifecycle_status`, `started_at`, `finished_at`) or denormalized fast-cache mirrors. Behavior diverges from `create_solver_run`, which always starts from `PENDING` with empty fast-cache kwargs.

## Scope

Mirror `create_solver_run` field assignment on reused rows when `overwrite=True`, minus row creation.

## Non-goals

- Changing `create_or_replace_solver_run` semantics.
- Altering no-overwrite idempotent path in `replay_pipeline_service`.

## Implementation Plan

1. Extract a small helper (optional) or inline block in `resolve_inspection_solver_run` that applies inspection scaffolding to an existing `SolverRun` instance:
   - `algorithm_label` from arg
   - `config_json` from `dict(config or {})`
   - `status = SolverRun.RunStatus.PENDING`
   - `artifact_root = ""`, `lifecycle_status = ""`
   - `started_at = None`, `finished_at = None`
   - fast-cache fields from `empty_solver_run_fast_cache_kwargs()`
2. Call `sync_solver_run_fast_cache_from_config_json(run)` after assignment (same order as `create_solver_run`).
3. Use `save(update_fields=[...])` listing all mutated columns to avoid clobbering unrelated state.
4. Confirm DTO returned by `_solver_run_dto` reflects updated `algorithm_label`, `status`, and `config_json`.
5. Add focused unit test in `tests/unit/asteroid_lab/test_experiment_service.py`: seed run with `algorithm_label="stale"`, `config_json={"old": true}`, `status=COMPLETED` → overwrite with new label/config → assert ORM fields match new args and `PENDING`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `tests/unit/asteroid_lab/test_experiment_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps/asteroid_lab/services/experiment_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v -k overwrite`
- build: `python manage.py check`
- manual verification: N/A (covered by unit test)

## Acceptance Criteria

- [ ] `algorithm_label` and `config` applied on overwrite.
- [ ] ORM lifecycle fields reset to inspection scaffolding.
- [ ] Fast-cache mirrors cleared via `empty_solver_run_fast_cache_kwargs()` + sync.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No change to no-overwrite idempotent path.

## Risks / Open Questions

- Whether `metric_snapshots` cascade should be cleared on overwrite (not mentioned in issue spec; defer unless tests fail).
