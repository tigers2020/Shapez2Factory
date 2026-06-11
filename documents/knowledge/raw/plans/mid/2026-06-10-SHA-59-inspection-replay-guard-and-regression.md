---
linear_issue: SHA-59
title: Inspection replay — fix expected frames constant and add regression test
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix `_INSPECTION_EXPECTED_FRAMES` and add trim-reconstruction regression

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment assumes one decode + four cleanup/reconstruction frames, but `record_decoded_snapshot_frames` appends two decode frames. The constant and missing event-type checklist allow incomplete replays to pass idempotency.

## Scope

- Fix `_INSPECTION_EXPECTED_FRAMES` and/or add event-type completeness checklist.
- Add pytest: build full replay, trim reconstruction frames to five, assert second `build_initial_replay_for_map_input` returns `failed` without `force=True`.

## Non-goals

- Frame emission count changes.
- SHA-50 overwrite semantics.

## Implementation Plan

1. Update `_INSPECTION_EXPECTED_FRAMES` to >= 6; fix stale module comment.
2. Implement `_inspection_replay_is_complete(track)` helper checking frame count and required `event_type` markers.
3. Wire helper into idempotent fast-path before returning `status="ok"`.
4. Add `test_build_initial_replay_rejects_partial_track_without_reconstruction`: full build → delete reconstruction frames → second call fails.
5. Add `test_build_initial_replay_force_rebuilds_partial_track`: same setup with `force=True` succeeds.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v -k inspection`
- lint/typecheck: per AGENTS.md gates on touched files

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Regression test for trim-reconstruction scenario.
- [ ] `force=True` rebuild path unchanged.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Canonical frame checklist should be documented in low-priority plan.
