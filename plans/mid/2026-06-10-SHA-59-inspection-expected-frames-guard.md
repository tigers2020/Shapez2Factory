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

# Plan: Fix _INSPECTION_EXPECTED_FRAMES and add completeness checklist

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment assumes one decode + four cleanup/reconstruction frames, but decode now records two frames. Count-only guard is stale.

## Scope

Update constant and add event-type completeness validation before idempotent return.

## Non-goals

- Frame emission count changes.

## Implementation Plan

1. Update `_INSPECTION_EXPECTED_FRAMES` to `6` (or derive from shared constant used by tests).
2. Extract helper `_inspection_replay_is_complete(track) -> bool` checking:
   - frame count threshold
   - required `event_type` markers include at least one reconstruction event
3. Replace `n >= _INSPECTION_EXPECTED_FRAMES` with helper call in idempotent branch.
4. Add pytest `test_build_initial_replay_rejects_partial_five_frame_track`:
   - Build full replay
   - Delete reconstruction frames leaving 5
   - Second `build_initial_replay_for_map_input` returns `failed` (not `ok`)
   - `force=True` still rebuilds successfully

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v -k partial`
- lint/typecheck: spot-check changed modules

## Acceptance Criteria

- [ ] Constant and/or checklist fix implemented.
- [ ] Regression test for trim-reconstruction scenario.
- [ ] Complete replays idempotent.

## Risks / Open Questions

- Exact reconstruction `event_type` strings — confirm from `existing_layout_service` / frame models before coding checklist.
