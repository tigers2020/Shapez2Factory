---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Mid
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fix inspection replay completeness guard and add regression test

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment assumes one decode frame plus four cleanup/reconstruction frames, but `record_decoded_snapshot_frames` appends two decode frames. No regression test covers trim-reconstruction scenario.

## Scope

Fix `_INSPECTION_EXPECTED_FRAMES` and/or add event-type completeness checklist; add pytest for trim-reconstruction → second call fails without `force=True`.

## Non-goals

- Changing `record_decoded_snapshot_frames` emission count.
- Altering `force=True` rebuild semantics.

## Implementation Plan

1. Update `_INSPECTION_EXPECTED_FRAMES` to documented minimum (>= 6).
2. Add helper to verify required `event_type` markers (at least one reconstruction event) before idempotent return.
3. Add pytest: build full replay (13 frames), delete reconstruction frames leaving 5.
4. Assert second `build_initial_replay_for_map_input` returns `failed` with incomplete message.
5. Assert `force=True` still rebuilds successfully.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (reference)
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Canonical frame checklist should align with `test_build_initial_replay_creates_run_track_frames_and_snapshots` (>= 6 frames).
