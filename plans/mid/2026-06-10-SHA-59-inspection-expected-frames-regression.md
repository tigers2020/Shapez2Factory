---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix _INSPECTION_EXPECTED_FRAMES and add trim-reconstruction regression

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment assumes one decode + four cleanup/reconstruction frames, but `record_decoded_snapshot_frames` appends two decode frames. Guard passes on 5-frame partial tracks without reconstruction events.

## Scope

1. Update `_INSPECTION_EXPECTED_FRAMES` and/or add event-type completeness checklist in `replay_pipeline_service.py`.
2. Add pytest: build full replay, delete reconstruction frames leaving 5 frames, second `build_initial_replay_for_map_input` returns `failed` without `force=True`.

## Non-goals

- Do not change frame emission pipeline.
- Do not change `force=True` rebuild path behavior beyond fixing false-positive `ok`.

## Implementation Plan

1. Update constant and inline comment to reflect two decode frames + reconstruction requirement.
2. Extract `_inspection_replay_is_complete(track)` helper if guard logic grows (frame count + event types).
3. In `tests/unit/asteroid_lab/test_replay_pipeline_service.py`, add `test_build_initial_replay_rejects_five_frame_partial_without_reconstruction`:
   - Run full `build_initial_replay_for_map_input` (existing fixture pattern).
   - Delete frames with reconstruction `event_type` until count is 5.
   - Second call without `force` asserts `status != "ok"` and incomplete error message.
4. Add positive control: complete replay second call still `ok`.
5. Run: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (reference)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: N/A
- manual verification: N/A if regression test covers trim scenario

## Acceptance Criteria

- [ ] `_INSPECTION_EXPECTED_FRAMES` and/or event-type checklist fixed.
- [ ] Regression test for trim-reconstruction scenario passes.
- [ ] `force=True` rebuild path unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test DB setup must preserve `ReconstructedAsteroidMap` row while trimming frames to reproduce idempotent path.
