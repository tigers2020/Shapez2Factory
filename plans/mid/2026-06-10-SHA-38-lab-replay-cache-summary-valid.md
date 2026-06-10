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

# Plan: Unify is_cache_summary_valid across lab replay composed-frame load paths

## Source Issue

- Linear: SHA-38
- Status at planning time: In Progress (triggered from Todo)
- Priority: Mid

## Problem

`load_composed_frames_for_run_id` applies inconsistent cache validity rules between the dedicated `lab_replay_payload_json` column path and the legacy `config_json` fallback path. When composed frames live in `lab_replay_payload_json`, the loader returns them after renderability and stale L3 thin-cache checks only. The `config_json` fallback additionally requires `is_cache_summary_valid(manifest_summary)` before returning frames.

Any caller that trusts `load_composed_frames_for_run_id`—including `build_asteroid_lab_page_context`, `entry_result_to_json_dict` inline mode, and `public_pages` lazy replay—can receive schema-stale composed replay from the column path even when manifest summary lacks `lab_replay_cache_schema_version`.

## Scope

Unify `load_composed_frames_for_run_id` so the dedicated-column path also requires `is_cache_summary_valid` on `lab_replay_manifest_summary_json` (already fetched on the same row query) before returning composed frames. Update unit tests that currently codify accepting invalid schema on the column path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Broad replay compose pipeline refactor.
- Fixing only page-context gating without aligning the loader (SHA-37 may remain until this lands or both are fixed together).

## Implementation Plan

1. In `load_composed_frames_for_run_id` (`lab_replay_persisted_cache.py` lines 148–157), after renderability and stale-thin-L3 checks on the column-path frames, read `lab_replay_manifest_summary_json` from the same `row` and return `None` unless `is_cache_summary_valid(summary)`.
2. Keep config-json fallback behavior unchanged (already enforces `is_cache_summary_valid`).
3. Update `test_dedicated_payload_wins_over_legacy_config_cache` in `test_artifact_first_replay.py`: either expect `None` when manifest lacks `lab_replay_cache_schema_version`, or seed a valid manifest summary (`lab_replay_cache_schema_version: CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`) when asserting column-path precedence over stale config cache.
4. Add or extend regression test confirming column path rejects schema-stale manifest (mirror existing config-path rejection in `test_artifact_jsonl_mode_rejects_stale_cache_without_schema_version` pattern).
5. Run `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (`load_composed_frames_for_run_id`, `is_cache_summary_valid`, `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`)
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- build: `python manage.py check`
- manual verification: Confirm lab page and lazy replay endpoints return `None`/recompose path when manifest lacks schema version on column-stored frames.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Rows with valid column payload but missing manifest summary will start returning `None`; recoverable via recompose.
- SHA-37 (page-context consumer guard) remains a separate card; fixing loader here may make SHA-37 redundant but both can land independently.
