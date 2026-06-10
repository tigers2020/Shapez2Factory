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

# Plan: Unify lab replay cache summary validation on dedicated-column load path

## Source Issue

- Linear: SHA-38
- Status at planning time: Todo
- Priority: Mid

## Problem

`load_composed_frames_for_run_id` applies inconsistent cache validity rules between the dedicated `lab_replay_payload_json` column path and the legacy `config_json` fallback path. When composed frames live in `lab_replay_payload_json`, the loader returns them after renderability and stale L3 thin-cache checks only. The `config_json` fallback additionally requires `is_cache_summary_valid(manifest_summary)` before returning frames.

Callers that trust `load_composed_frames_for_run_id`—including `build_asteroid_lab_page_context`, `entry_result_to_json_dict` inline mode, and `public_pages` lazy replay—can receive schema-stale composed replay from the column path even when manifest summary lacks `lab_replay_cache_schema_version`.

## Scope

Unify `load_composed_frames_for_run_id` so the dedicated-column path also requires `is_cache_summary_valid` on `lab_replay_manifest_summary_json` (already fetched on the same row query) before returning composed frames. Update unit tests that currently codify accepting invalid schema on the column path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Broad replay compose pipeline refactor.
- Fixing only page-context gating without aligning the loader (SHA-37 may remain until this lands or both are fixed together).

## Implementation Plan

1. Open `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` and locate `load_composed_frames_for_run_id` column branch (lines ~148–157).
2. After existing `lab_replay_frames_are_renderable` and `_is_stale_thin_artifact_l3_cache` checks, read `summary = _dict_or_none(row.get("lab_replay_manifest_summary_json"))` and return `None` unless `is_cache_summary_valid(summary)`.
3. Keep the legacy `config_json` fallback path unchanged (it already enforces `is_cache_summary_valid`).
4. Update `tests/unit/asteroid_lab/test_artifact_first_replay.py::test_dedicated_payload_wins_over_legacy_config_cache`:
   - Seed `lab_replay_manifest_summary_json` with a valid summary including `lab_replay_cache_schema_version: CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION` (import from `lab_replay_persisted_cache`) so column-path precedence over stale config is still asserted under the unified contract.
5. Add regression test (same file or `test_lab_replay_persisted_cache.py`): dedicated payload with renderable frames but manifest `{"frame_count": 1}` (no schema version) returns `None` from `load_composed_frames_for_run_id`.
6. Run focused tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (`load_composed_frames_for_run_id`, `is_cache_summary_valid`, `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`)
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`
- `tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py tests/unit/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py -v`
- build: `python manage.py check`
- manual verification: Confirm a run with stale manifest schema no longer serves composed frames via page context or lazy replay endpoints.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Runs with dedicated payload but missing/invalid manifest summary will stop serving cached frames until recompose; expected and recoverable.
- SHA-37 (page-context consumer guard) remains a separate card; loader fix is the source-of-truth alignment.
- `invariant:` replay cache schema bumps must continue to version via `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`.
