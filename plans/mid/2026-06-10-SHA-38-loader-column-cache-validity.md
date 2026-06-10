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

# Plan: Unify load_composed_frames_for_run_id cache validity on column path

## Source Issue

- Linear: SHA-38
- Status at planning time: In Progress
- Priority: Mid

## Problem

`load_composed_frames_for_run_id` applies inconsistent cache validity rules between the dedicated `lab_replay_payload_json` column path and the legacy `config_json` fallback path. Column path returns frames after renderability and stale L3 checks only; config fallback additionally requires `is_cache_summary_valid(manifest_summary)`.

## Scope

Unify `load_composed_frames_for_run_id` so the dedicated-column path also requires `is_cache_summary_valid` on manifest summary before returning composed frames. Update unit tests that codify accepting invalid schema on the column path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Broad replay compose pipeline refactor.
- Consumer-only gating without aligning loader (SHA-37 may land separately).

## Implementation Plan

1. In `lab_replay_persisted_cache.py` column branch (lines 148–157), read `lab_replay_manifest_summary_json` from the same row query.
2. Return `None` unless `is_cache_summary_valid(summary)` in addition to renderability and stale L3 thin-cache checks.
3. Update `test_dedicated_payload_wins_over_legacy_config_cache`: seed valid `lab_replay_cache_schema_version` on manifest when asserting column-path precedence, or expect `None` when schema version missing.
4. Run `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`
- `tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/unit/asteroid_lab/test_lab_replay_persisted_cache.py -v`
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate landing with SHA-37 to avoid transient double-recompose.
- `solver_runtime_entry` inline branch may benefit automatically once loader is fixed.
