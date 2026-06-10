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

# Plan: Reset SolverRun lifecycle and fast-cache mirrors on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Mid

## Problem

The overwrite branch in `resolve_inspection_solver_run` deletes replay frames only and ignores `algorithm_label` and `config` arguments. Reused rows retain prior solver lifecycle state and denormalized cache columns instead of mirroring `create_solver_run` scaffolding.

## Scope

Reset all relevant `SolverRun` ORM lifecycle fields and fast-cache mirrors when `overwrite=True` reuses an existing row. Apply passed `algorithm_label` and `config`, then sync fast-cache from config.

## Non-goals

- Changing `create_or_replace_solver_run` semantics.
- Modifying SHA-37/SHA-38 read-path cache validity.
- Changing no-overwrite idempotent path in `replay_pipeline_service`.

## Implementation Plan

1. Extract or inline a private helper (optional) `_reset_solver_run_for_inspection_overwrite(run, *, algorithm_label, config)` adjacent to `resolve_inspection_solver_run` to keep overwrite branch readable — mirror `create_solver_run` field assignment minus row creation.
2. Reset lifecycle fields:
   - `status` → `SolverRun.RunStatus.PENDING`
   - `artifact_root` → `""`
   - `lifecycle_status` → `""`
   - `started_at` → `None`
   - `finished_at` → `None`
3. Assign `algorithm_label` from argument (do not leave prior solver label).
4. Assign `config_json = dict(config or {})`.
5. Apply fast-cache reset via `**empty_solver_run_fast_cache_kwargs()` field assignment on the in-memory `run` instance.
6. Call `sync_solver_run_fast_cache_from_config_json(run)` to mirror any config keys onto denormalized columns (matches `create_solver_run` sequence).
7. `run.save(update_fields=[...])` with the full set of mutated fields.
8. After save, delete frames on matching `ReplayTrack` and call `ensure_default_replay_track` as today.
9. Return `_solver_run_dto(run, replay_track_id=ref.track_id)` with updated values reflected in DTO.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py`
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- `django_apps/asteroid_lab/services/solver_run_config_keys.py` (reference only)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps/asteroid_lab/services/experiment_service.py django_apps/asteroid_lab/services/solver_run_fast_cache.py`
- tests: covered in Low-priority regression test plan; run after implementation
- build: `python manage.py check`
- manual verification: Assert `algorithm_label` and `config_json` on reused row match call args after overwrite

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Order of operations: reset fields before frame delete vs after — either is fine if atomic under `@transaction.atomic`.
- If `config` contains pre-populated replay keys, `sync_solver_run_fast_cache_from_config_json` may repopulate columns intentionally; empty inspection `config` should yield empty cache.
