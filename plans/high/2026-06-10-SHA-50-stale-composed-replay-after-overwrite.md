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
- Status at planning time: In Progress (moved from Todo by backlog automation)
- Priority: High

## Problem

`resolve_inspection_solver_run(..., overwrite=True)` reuses an existing `SolverRun` row but only deletes `ReplayFrame` rows. It leaves `status=COMPLETED`, denormalized fast-cache columns (`solver_summary_json`, `lab_replay_payload_json`, `lab_replay_manifest_summary_json`, `solver_runtime_replay_frames_json`), and lifecycle/artifact pointers intact. After a prior solver execution warmed cache onto the inspection `run_key`, map overwrite / inspection rebuild can record new frames while Lab loaders still read prior composed replay from column fast-cache (related read-path issues: SHA-37, SHA-38).

## Scope

Ensure overwrite resets the reused `SolverRun` row to empty inspection scaffolding before the replay pipeline re-records frames, so column fast-cache cannot serve prior solver output.

## Non-goals

- Changing `create_or_replace_solver_run` delete-and-recreate semantics.
- Reworking `load_composed_frames_for_run_id` validity rules (SHA-37/SHA-38).
- Altering idempotent no-overwrite short-circuit in `replay_pipeline_service`.

## Implementation Plan

1. In `django_apps/asteroid_lab/services/experiment_service.py`, extend the `overwrite=True` branch of `resolve_inspection_solver_run` (lines 146–153) to reset lifecycle and fast-cache fields on the reused row **after** `track.frames.all().delete()` and **before** `ensure_default_replay_track`.
2. Set `run.status = SolverRun.RunStatus.PENDING`.
3. Clear lifecycle mirrors: `artifact_root=""`, `lifecycle_status=""`, `started_at=None`, `finished_at=None`.
4. Apply `algorithm_label` and `config_json=dict(config or {})` from call args (currently ignored on overwrite).
5. Reset fast-cache columns via `empty_solver_run_fast_cache_kwargs()` spread onto the row, then call `sync_solver_run_fast_cache_from_config_json(run)` so config mirrors match `create_solver_run`.
6. `run.save()` with explicit `update_fields` covering status, config, lifecycle, and all four fast-cache columns.
7. Verify `build_initial_replay_for_map_input(..., overwrite=True)` path in `replay_pipeline_service.py` needs no change (caller already passes config/label).
8. Manual repro: seed completed run with stale `lab_replay_payload_json` → overwrite → confirm Lab column loaders see empty composed frames until pipeline re-persists.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py` (`resolve_inspection_solver_run`)
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py` (`empty_solver_run_fast_cache_kwargs`, `sync_solver_run_fast_cache_from_config_json`)
- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (caller verification only)
- `django_apps/asteroid_lab/models.py` (`SolverRun` lifecycle fields)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/experiment_service.py`
- typecheck: `mypy django_apps/asteroid_lab/services/experiment_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: `python manage.py check`
- manual verification: Seed COMPLETED run with composed cache → `resolve_inspection_solver_run(..., overwrite=True)` → columns empty, status pending

## Acceptance Criteria

- [ ] Overwrite clears stale fast-cache columns and resets status to inspection scaffolding.
- [ ] Lab loaders cannot read prior composed replay from column fast-cache immediately after overwrite.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `SolverMetricSnapshot` rows on the reused run are not deleted by overwrite today; confirm whether stale metric snapshots can still leak via other loaders (out of scope unless repro shows user impact).
- SHA-37/SHA-38 read-path guards remain separate; this plan fixes the overwrite write-path root cause.
