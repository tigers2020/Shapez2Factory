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

# Plan: Reset ORM lifecycle and apply config on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Mid

## Problem

The overwrite branch in `resolve_inspection_solver_run` ignores `algorithm_label` and `config` arguments and leaves ORM lifecycle fields (`status`, timestamps, artifact pointers) unchanged when reusing an existing row.

## Scope

Reset ORM lifecycle fields and fast-cache mirrors on overwrite. Apply `algorithm_label` and `config` on the reused row, mirroring `create_solver_run` minus row creation.

## Non-goals

- `create_or_replace_solver_run` semantics.
- Read-path cache validity (SHA-37/SHA-38).

## Implementation Plan

1. Open `django_apps/asteroid_lab/services/experiment_service.py` — locate `resolve_inspection_solver_run`.
2. Import/use `empty_solver_run_fast_cache_kwargs()` from `solver_run_fast_cache.py`.
3. In `overwrite=True` branch after frame delete:
   ```python
   run.status = SolverRunStatus.PENDING  # match create_solver_run
   run.algorithm_label = algorithm_label
   run.config_json = config
   for field, value in empty_solver_run_fast_cache_kwargs().items():
       setattr(run, field, value)
   sync_solver_run_fast_cache_from_config_json(run)  # if create_solver_run does this
   run.save(update_fields=[...])
   ```
4. Clear lifecycle timestamps / artifact FKs per `create_solver_run` pattern.
5. Compare field list with `create_solver_run` to avoid drift.
6. Run: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps/asteroid_lab/services/experiment_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: N/A
- manual verification: overwrite applies new algorithm_label/config

## Acceptance Criteria

- [ ] `algorithm_label` and `config` applied on overwrite.
- [ ] ORM lifecycle fields reset to inspection scaffolding.
- [ ] Matches the source issue spec.
- [ ] No change to no-overwrite idempotent path.

## Risks / Open Questions

- `update_fields` list must include all mutated columns for partial save correctness.
