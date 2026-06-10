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

`resolve_inspection_solver_run(..., overwrite=True)` reuses the existing `SolverRun` row but only deletes `ReplayFrame` rows. It does not reset `status`, fast-cache columns, or lifecycle fields. After a prior solver execution, map overwrite can leave stale `COMPLETED` status and composed replay cache while new inspection frames are recorded. Lab loaders reading column fast-cache can serve prior solver output.

## Scope

Ensure overwrite path resets solver lifecycle and fast-cache mirrors to empty inspection scaffolding before replay pipeline re-records frames. This is the root-cause fix for stale data served after rebuild (distinct from SHA-37/SHA-38 read-path validity guards).

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics.
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`.

## Implementation Plan

1. Read `resolve_inspection_solver_run` overwrite branch in `experiment_service.py` (~146–153).
2. After `track.frames.all().delete()`, reset:
   - `run.status = SolverRunStatus.PENDING` (or equivalent inspection scaffolding)
   - Clear lifecycle timestamps and artifact pointers
   - Apply `empty_solver_run_fast_cache_kwargs()` to denormalized columns
3. Assign passed `algorithm_label` and `config_json`; call `sync_solver_run_fast_cache_from_config_json` if used by `create_solver_run`.
4. `run.save()` before returning DTO.
5. Verify `build_initial_replay_for_map_input(..., overwrite=True)` path picks up reset row.
6. Run regression test from Low plan slice.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (caller verification)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps/asteroid_lab/services/experiment_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v -k overwrite`
- build: N/A
- manual verification: seed completed run with cache → overwrite → confirm Lab does not show prior solver output

## Acceptance Criteria

- [ ] Overwrite clears stale fast-cache columns and resets status to inspection scaffolding.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Mid plan must apply config/algorithm_label consistently with `create_solver_run`.
- Coordinate with SHA-37/SHA-38 if read-path guards also need updates (out of scope unless overwrite fix insufficient).
