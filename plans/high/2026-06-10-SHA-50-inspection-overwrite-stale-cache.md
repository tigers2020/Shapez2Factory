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

# Plan: Stop serving stale composed replay after inspection map overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` reuses the existing `SolverRun` row but only deletes `ReplayFrame` rows. It does not reset `status`, fast-cache columns, or lifecycle pointers. After a prior solver execution warms cache onto the inspection `run_key`, map overwrite can leave stale `COMPLETED` status and composed replay cache while new inspection frames are recorded.

## Scope

Ensure overwrite path clears stale solver lifecycle and fast-cache mirrors so Lab loaders cannot serve prior solver output for a rebuilt map.

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics.
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Altering idempotent no-overwrite short-circuit.

## Implementation Plan

1. Reproduce with pytest: seed `SolverRun` with `status=completed` and populated fast-cache columns → `resolve_inspection_solver_run(..., overwrite=True)` → assert columns unchanged (current bug).
2. In `experiment_service.py` overwrite branch, after frame delete: set `status=PENDING`, clear artifact/lifecycle timestamps.
3. Apply `empty_solver_run_fast_cache_kwargs()` or equivalent to clear denormalized JSON columns.
4. Verify `replay_pipeline_service.build_initial_replay_for_map_input` overwrite path serves fresh inspection scaffolding.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (caller verification)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: N/A
- manual verification: Map overwrite after completed solver does not show prior composed replay

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Overwrite clears stale fast-cache columns and resets status to inspection scaffolding.
- [ ] No change to no-overwrite idempotent path.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Mid plan covers `algorithm_label`/`config` application; implement together with this fix.
