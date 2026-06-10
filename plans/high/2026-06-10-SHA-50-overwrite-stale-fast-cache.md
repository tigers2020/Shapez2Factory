---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: High
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Clear stale solver fast-cache on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` deletes replay frames only. Stale `COMPLETED` status and fast-cache columns (`solver_summary_json`, `lab_replay_payload_json`, etc.) remain, so Lab can serve prior solver output after map rebuild.

## Scope

Reset `SolverRun` lifecycle and fast-cache mirrors when `overwrite=True` reuses an existing row.

## Non-goals

- `create_or_replace_solver_run` delete-and-recreate semantics.
- `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- No-overwrite idempotent path in `replay_pipeline_service`.

## Implementation Plan

1. Read `resolve_inspection_solver_run` overwrite branch in `experiment_service.py` (~146–153).
2. After `track.frames.all().delete()`: set `status=PENDING`, clear artifact/lifecycle timestamps.
3. Apply `algorithm_label`, `config_json`; call `empty_solver_run_fast_cache_kwargs()` or `sync_solver_run_fast_cache_from_config_json`.
4. `save()` before returning DTO.
5. Repro test: seed completed run with stale cache → overwrite → assert columns empty.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `tests/unit/asteroid_lab/test_experiment_service.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`

## Acceptance Criteria

- [ ] Overwrite clears stale fast-cache and resets status.
- [ ] No change to no-overwrite path.

## Risks / Open Questions

- Related SHA-37/38 may still need separate fixes for read-path validity.
