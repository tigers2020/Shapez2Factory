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

# Plan: Reset ORM lifecycle and fast-cache mirrors on overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Mid

## Problem

Overwrite branch in `resolve_inspection_solver_run` deletes frames only (`track.frames.all().delete()`), ignores `algorithm_label` / `config` args, and returns DTO for unchanged row. Repro pytest: seed completed run with stale fast-cache → `resolve_inspection_solver_run(..., overwrite=True)` → columns unchanged.

## Scope

In the `overwrite=True` branch, after frame delete: reset solver lifecycle ORM fields and fast-cache mirrors to empty inspection scaffolding, apply passed `algorithm_label` and `config_json`, sync fast-cache from config, then `save()`.

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics.
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`.

## Implementation Plan

1. Read `resolve_inspection_solver_run` overwrite branch at `experiment_service.py` lines 146–153 and `create_solver_run` for target field set.
2. After `track.frames.all().delete()`:
   - Set `run.status = PENDING` (or inspection scaffolding enum).
   - Clear artifact/lifecycle timestamps and pointers as `create_solver_run` does.
   - Apply `kwargs` from `empty_solver_run_fast_cache_kwargs()` to clear `solver_summary_json`, `lab_replay_payload_json`, `lab_replay_manifest_summary_json`, `solver_runtime_replay_frames_json`.
3. Assign `algorithm_label` and `config_json` from function args (currently ignored on overwrite).
4. Call `sync_solver_run_fast_cache_from_config_json(run)` after reset.
5. `run.save()` and return updated DTO.
6. Confirm `replay_pipeline_service.build_initial_replay_for_map_input(..., overwrite=True)` caller sees reset row before re-recording frames.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py` (`resolve_inspection_solver_run`, lines 146–153)
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (caller reference)
- `tests/unit/asteroid_lab/test_experiment_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: `python manage.py check`
- manual verification: N/A (covered by regression test in Low scope)

## Acceptance Criteria

- [ ] Overwrite branch resets lifecycle fields and fast-cache columns.
- [ ] `algorithm_label` and `config_json` applied on reused row.
- [ ] Behavior mirrors `create_solver_run` minus row creation.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Field list in `empty_solver_run_fast_cache_kwargs()` must stay in sync with new denormalized columns.
- Overwrite currently preserves `run_key` — confirm callers depend on stable key and not on preserved status.
