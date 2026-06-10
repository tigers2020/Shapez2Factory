---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: High
labels:
  - bug
  - test
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Stop serving stale composed replay after map overwrite rebuild

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` reuses the existing `SolverRun` row but only deletes `ReplayFrame` rows on the matching `ReplayTrack`. It does not reset `status`, `algorithm_label`, `config_json`, denormalized fast-cache columns (`solver_summary_json`, `lab_replay_payload_json`, `lab_replay_manifest_summary_json`, `solver_runtime_replay_frames_json`), or lifecycle/artifact pointers.

After a prior solver execution indexes warm-cache onto the inspection `run_key`, map overwrite / inspection rebuild can leave stale `COMPLETED` status and composed replay cache on the row while new inspection frames are recorded. Lab loaders that read column fast-cache (SHA-37/SHA-38) can then serve prior solver output for the rebuilt map.

## Scope

Ensure map overwrite rebuild clears stale solver lifecycle and fast-cache mirrors on the reused `SolverRun` row before replay pipeline re-records frames. Operators must not see prior solver composed replay or `COMPLETED` status after inspection rebuild.

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics.
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`.

## Implementation Plan

1. Repro: seed `SolverRun` with `status=completed`, `solver_summary_json={"stale": true}`, populated `lab_replay_payload_json` → call `resolve_inspection_solver_run(..., overwrite=True)` → confirm columns unchanged (current bug).
2. In `experiment_service.py` overwrite branch (lines 146–153), after `track.frames.all().delete()`, reset ORM lifecycle fields to inspection scaffolding (`status=PENDING`, clear artifact/lifecycle timestamps).
3. Clear fast-cache columns via `empty_solver_run_fast_cache_kwargs()` or equivalent reset before applying new config.
4. Apply passed `algorithm_label` and `config_json`; call `sync_solver_run_fast_cache_from_config_json` after reset; `save()`.
5. Verify Lab page / `load_composed_frames_for_run_id` no longer returns prior composed replay after overwrite rebuild.
6. Mirror behavior of `create_solver_run` minus row creation.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py` (`resolve_inspection_solver_run`, `ensure_default_replay_track`)
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py` (`empty_solver_run_fast_cache_kwargs`, `sync_solver_run_fast_cache_from_config_json`)
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (`build_initial_replay_for_map_input`, `overwrite=True` path)
- `tests/unit/asteroid_lab/test_experiment_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: `python manage.py check`
- manual verification: Run solver to completion on inspection run, overwrite map input, confirm Lab shows inspection replay not prior solver output.

## Acceptance Criteria

- [ ] Overwrite clears stale fast-cache columns and resets status to inspection scaffolding.
- [ ] `algorithm_label` and `config` applied on overwrite.
- [ ] No change to no-overwrite idempotent path.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-37/SHA-38 consumer guards may mask but not fix root cause if stale column cache remains on row.
- Artifact pointer reset must not break in-flight async solver unless overwrite is intended to supersede (confirm caller contract).
