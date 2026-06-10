---
linear_issue: SHA-38
title: load_composed_frames_for_run_id column path skips is_cache_summary_valid
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unify lab replay cache validity on column path

## Source Issue

- Linear: SHA-38
- Status at planning time: Todo
- Priority: Mid

## Problem

`load_composed_frames_for_run_id` enforces `is_cache_summary_valid` on the `config_json` fallback path but not on the dedicated `lab_replay_payload_json` column path. Callers can load schema-stale composed replay when frames live in the column.

## Scope

Unify loader so column path also requires `is_cache_summary_valid` on manifest summary before returning frames. Update tests that codify invalid-schema acceptance on column path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Broad replay compose pipeline refactor.
- Page-context-only guard without loader fix (SHA-37).

## Implementation Plan

1. In `lab_replay_payload_json` branch of `load_composed_frames_for_run_id`, load `lab_replay_manifest_summary_json`.
2. Return `None` unless `is_cache_summary_valid(summary)` in addition to renderability / stale L3 checks.
3. Update `test_dedicated_payload_wins_over_legacy_config_cache`: expect `None` when manifest lacks schema version, or seed valid manifest when asserting column precedence.
4. Run `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- tests: `python -m pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-37 page-context guard to avoid duplicate/conflicting fixes.
