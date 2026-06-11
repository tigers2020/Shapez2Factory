---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix inspection replay completeness guard and add regression test

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` is stale (assumes one decode frame). No event-type validation before idempotent return.

## Scope

Update `_INSPECTION_EXPECTED_FRAMES` and/or add reconstruction event checklist; add pytest for trim-reconstruction scenario.

## Non-goals

- Changing frame emission counts.
- SHA-50 overwrite semantics.
- Artifact ingest changes.

## Implementation Plan

1. Extract `_inspection_replay_is_complete(track)` helper checking frame count and required `event_type` markers.
2. Replace raw `frames.count() >= _INSPECTION_EXPECTED_FRAMES` with helper in `build_initial_replay_for_map_input`.
3. Return existing incomplete failure message when guard fails (unless `force=True`).
4. Add test: full replay → delete reconstruction frames → second call returns `failed` without `force=True`.
5. Add test: complete replay still idempotently returns `ok`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Canonical event list must match production pipeline; confirm against `test_build_initial_replay_creates_run_track_frames_and_snapshots`.
