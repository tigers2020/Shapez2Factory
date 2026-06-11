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

# Plan: Fix stale composed replay and COMPLETED status after map overwrite rebuild

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` reuses an existing `SolverRun` row but only deletes `ReplayFrame` rows. It leaves `status=COMPLETED`, denormalized fast-cache columns (`solver_summary_json`, `lab_replay_payload_json`, `lab_replay_manifest_summary_json`, `solver_runtime_replay_frames_json`), and lifecycle/artifact pointers unchanged. After a prior solver execution warms the inspection `run_key`, map overwrite / inspection rebuild can record new frames while Lab loaders that read column fast-cache (related: SHA-37, SHA-38) still serve prior solver output.

## Scope

Ensure overwrite path resets the reused `SolverRun` to empty inspection scaffolding so Lab page context and `load_composed_frames_for_run_id` column paths cannot serve stale composed replay or a false COMPLETED status after rebuild.

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics.
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`.

## Implementation Plan

1. In `django_apps/asteroid_lab/services/experiment_service.py`, extend the `overwrite=True` branch of `resolve_inspection_solver_run` (lines 146–153) to reset lifecycle and fast-cache fields on the reused row before returning the DTO.
2. Set `run.status = SolverRun.RunStatus.PENDING`.
3. Clear `artifact_root`, `lifecycle_status`, `started_at`, and `finished_at` to match fresh inspection scaffolding.
4. Apply `empty_solver_run_fast_cache_kwargs()` to reset all four fast-cache JSON columns to empty defaults (same as `create_solver_run`).
5. Assign `algorithm_label` and `config_json` from call arguments; call `sync_solver_run_fast_cache_from_config_json(run)` so config mirrors stay consistent.
6. `save()` with explicit `update_fields` covering all mutated columns.
7. Keep frame deletion and `ensure_default_replay_track` behavior unchanged; preserve `run_key` and row `id`.
8. Verify caller `replay_pipeline_service.build_initial_replay_for_map_input(..., overwrite=True)` needs no change if reset happens inside `resolve_inspection_solver_run`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py` (`resolve_inspection_solver_run`)
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py` (`empty_solver_run_fast_cache_kwargs`, `sync_solver_run_fast_cache_from_config_json`)
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (caller verification only)
- `django_apps/asteroid_lab/models.py` (`SolverRun` lifecycle fields — read-only reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v -k overwrite`
- build: `python manage.py check`
- manual verification: Seed `SolverRun` with `status=completed` and populated fast-cache columns → call `resolve_inspection_solver_run(..., overwrite=True)` → confirm `status=pending` and empty cache columns before replay pipeline re-records frames

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Related SHA-37/SHA-38 address read-path validity; this fix addresses the write-path root cause on overwrite.
- `SolverMetricSnapshot` rows are not deleted on overwrite; confirm whether stale metrics can leak (out of current spec — flag if observed).
- `invariant:` fast-cache columns remain UI/index only; reset must not affect solver algorithm input.
