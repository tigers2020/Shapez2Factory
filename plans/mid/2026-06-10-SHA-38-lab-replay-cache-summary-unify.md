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

# Plan: Unify lab replay cache validity on dedicated column path

## Source Issue

- Linear: SHA-38
- Status at planning time: Todo
- Priority: Mid

## Problem

`load_composed_frames_for_run_id` returns composed frames from `lab_replay_payload_json` after renderability and stale L3 thin-cache checks only. The legacy `config_json` fallback additionally requires `is_cache_summary_valid(manifest_summary)`. Callers (`build_asteroid_lab_page_context`, `entry_result_to_json_dict`, `public_pages`) can load schema-stale replay from the column path when manifest summary lacks `lab_replay_cache_schema_version`.

## Scope

Unify the dedicated-column path so it also requires `is_cache_summary_valid` on `lab_replay_manifest_summary_json` before returning frames. Update unit tests that currently codify invalid-schema acceptance on the column path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Broad replay compose pipeline refactor.
- Fixing only page-context gating without aligning the loader (SHA-37 may remain until this lands or both are fixed together).

## Implementation Plan

1. In `load_composed_frames_for_run_id`, after loading `lab_replay_payload_json` row data, read `lab_replay_manifest_summary_json` from the same row (already fetched in `.values()`).
2. Before returning frames from the column path, require `is_cache_summary_valid(summary)` in addition to `lab_replay_frames_are_renderable` and `not _is_stale_thin_artifact_l3_cache`.
3. Return `None` when manifest summary is missing or invalid schema version (match config fallback contract).
4. Update `test_dedicated_payload_wins_over_legacy_config_cache` in `tests/unit/asteroid_lab/test_artifact_first_replay.py`: seed a valid manifest summary (with `lab_replay_cache_schema_version` matching `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`) when asserting column-path precedence over legacy config.
5. Add regression test: column path with invalid/missing schema version returns `None` even when payload frames are renderable.
6. Run focused tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`
- `django_apps/asteroid_lab/services/solver_runtime_entry.py` (consumer; verify no extra changes needed)
- `django_apps/web/services/asteroid_lab_page_context.py` (consumer; verify behavior via loader)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- typecheck: `mypy django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- build: N/A
- manual verification: Lab page with dedicated payload + invalid manifest should not serve stale composed replay

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-37 (page-context consumer guard) may still need a follow-up if loader fix alone is insufficient for all code paths.
- Existing DB rows with dedicated payload but pre-schema manifest may stop serving replay until recompose; document as expected contract enforcement.
