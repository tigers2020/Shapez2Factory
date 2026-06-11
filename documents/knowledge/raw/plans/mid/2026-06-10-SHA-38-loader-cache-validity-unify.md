---
linear_issue: SHA-38
title: load_composed_frames_for_run_id column path skips is_cache_summary_valid (config fallback enforces it)
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unify loader cache validity across column and config paths

## Source Issue

- Linear: SHA-38
- Status at planning time: Todo
- Priority: Mid

## Problem

`load_composed_frames_for_run_id` applies inconsistent cache validity rules between the dedicated `lab_replay_payload_json` column path and the legacy `config_json` fallback path. When composed frames live in `lab_replay_payload_json`, the loader returns them after renderability and stale L3 thin-cache checks only. The `config_json` fallback additionally requires `is_cache_summary_valid(manifest_summary)` before returning frames. Callers including `build_asteroid_lab_page_context`, `entry_result_to_json_dict` inline mode, and `public_pages` lazy replay can receive schema-stale composed replay from the column path.

## Scope

Unify `load_composed_frames_for_run_id` so the dedicated-column path also requires `is_cache_summary_valid` on `lab_replay_manifest_summary_json` (or loaded manifest) before returning composed frames. Update/adjust unit tests that currently codify accepting invalid schema on the column path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Broad replay compose pipeline refactor.
- Fixing only page-context gating without aligning the loader (SHA-37 may remain until both land).

## Implementation Plan

1. In `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`, update the `lab_replay_payload_json` branch (lines 148–157) to load `lab_replay_manifest_summary_json` from the same row and return `None` unless `is_cache_summary_valid(summary)` in addition to renderability / stale L3 checks.
2. Confirm config fallback path (lines 170–178) remains unchanged — both paths must enforce identical contract.
3. Audit callers: `django_apps/asteroid_lab/services/solver_runtime_entry.py` (`entry_result_to_json_dict` inline branch lines 359–362), `django_apps/web/services/asteroid_lab_page_context.py`, `django_apps/web/views/public_pages.py`.
4. Update `tests/unit/asteroid_lab/test_artifact_first_replay.py::test_dedicated_payload_wins_over_legacy_config_cache` to expect `None` when manifest lacks schema version, or seed a valid manifest summary when asserting column-path precedence over config.
5. Add regression test covering column path rejection when `lab_replay_cache_schema_version` is missing or stale.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (`load_composed_frames_for_run_id`, `is_cache_summary_valid`, `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`)
- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- build: N/A
- manual verification: Run with dedicated payload column + invalid manifest returns cache miss and triggers recompose

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test change may break assumptions in SHA-37 page-context work — coordinate merge order.
- Multiple consumers may see increased recompose frequency until stale rows are backfilled (SHA-37 Low migration).
