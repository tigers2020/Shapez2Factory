---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: High
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Stop serving stale composed replay after map overwrite rebuild

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` reuses the existing `SolverRun` row but only deletes `ReplayFrame` rows. It does not reset `status`, fast-cache columns, or lifecycle pointers. After a prior solver execution indexes warm-cache onto the inspection `run_key`, map overwrite can leave stale `COMPLETED` status and composed replay cache while new inspection frames are recorded.

## Scope

Ensure overwrite path clears stale composed replay and resets solver lifecycle so Lab loaders cannot serve prior solver output for a rebuilt map.

## Non-goals

- Changing `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Changing `create_or_replace_solver_run` delete-and-recreate semantics.

## Implementation Plan

1. Reproduce with pytest: seed `SolverRun` with `status=completed` and populated fast-cache columns, call `resolve_inspection_solver_run(..., overwrite=True)`, assert columns unchanged (confirms bug).
2. Read `resolve_inspection_solver_run` overwrite branch in `django_apps/asteroid_lab/services/experiment_service.py` (lines 146–153).
3. After frame delete, reset `run.status` to inspection scaffolding (`PENDING` or equivalent).
4. Clear fast-cache mirrors via `empty_solver_run_fast_cache_kwargs()` from `solver_run_fast_cache.py`.
5. Clear artifact/lifecycle timestamps and pointers.
6. Verify Lab page context no longer serves stale composed replay after overwrite rebuild.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_experiment_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: `python manage.py check`
- manual verification: Map overwrite rebuild does not show prior solver COMPLETED cache

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-37/SHA-38 cache validity gaps may still allow stale reads via other code paths; this plan addresses overwrite root cause only.
