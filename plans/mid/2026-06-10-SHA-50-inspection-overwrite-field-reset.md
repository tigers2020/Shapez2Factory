---
linear_issue: SHA-50
title: resolve_inspection_solver_run overwrite retains stale SolverRun status and fast-cache columns
priority: Mid
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Reset SolverRun ORM fields and apply config on inspection overwrite

## Source Issue

- Linear: SHA-50
- Status at planning time: Todo
- Priority: Mid

## Problem

Overwrite branch ignores `algorithm_label` and `config` arguments and does not call `sync_solver_run_fast_cache_from_config_json` after reset.

## Scope

Mirror `create_solver_run` field assignment on reused row when `overwrite=True`.

## Non-goals

- Changing row creation vs reuse policy.
- Replay track semantics beyond frame delete.

## Implementation Plan

1. In `resolve_inspection_solver_run` overwrite branch, assign `algorithm_label` and `config_json` from call arguments.
2. Call `sync_solver_run_fast_cache_from_config_json` after fast-cache clear and before `save()`.
3. Compare field list with `create_solver_run` and `empty_solver_run_fast_cache_kwargs()` for parity.
4. Update `ensure_default_replay_track` interaction if track metadata depends on reset status.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/experiment_service.py` (`resolve_inspection_solver_run`, `ensure_default_replay_track`)
- `django_apps/asteroid_lab/services/solver_run_fast_cache.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_experiment_service.py -v`
- build: N/A
- manual verification: Overwrite applies new `algorithm_label` and empty cache

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] `algorithm_label` and `config` applied on overwrite.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `test_build_initial_replay_overwrite_keeps_run_key` may need extension — see Low plan.
