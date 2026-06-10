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

# Plan: Inspection completeness guard implementation and trim-reconstruction regression test

## Source Issue

- Linear: SHA-59
- Status at planning time: In Progress (moved from Todo by prior automation)
- Priority: Mid

## Problem

The `_INSPECTION_EXPECTED_FRAMES = 5` constant is stale relative to the current inspection pipeline (two decode frames, three cleanup snapshots, plus reconstruction events). Count-only guard allows truncated replays to pass idempotency.

## Scope

Implement the guard fix (`_INSPECTION_EXPECTED_FRAMES` bump and/or event-type completeness checklist) and add pytest coverage for the trim-reconstruction scenario.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- SHA-50 overwrite stale SolverRun cache fix.
- Broader replay timeline compose changes.

## Implementation Plan

1. Implement `_inspection_replay_is_complete` (or inline equivalent) in `replay_pipeline_service.py`:
   - Query ordered frames for the track.
   - Require `count >= 6`.
   - Require at least one frame whose `frame_payload["event_type"]` is in the reconstruction phase set (`EVENT_TYPE_RECONSTRUCTION_BEGIN`, `EVENT_TYPE_RECONSTRUCTION_SHELL_DETECTED`, etc. — mirror `test_build_initial_replay_creates_run_track_frames_and_snapshots`).
2. Wire helper into the idempotent fast-path before `_result_from_completed_track`.
3. Add `test_build_initial_replay_rejects_partial_track_without_reconstruction`:
   - Build full replay via `build_initial_replay_for_map_input`.
   - Delete frames whose `event_type` is in reconstruction phase set (or delete frames after cleanup snapshots).
   - Assert remaining frame count is 5 and no reconstruction events remain.
   - Second `build_initial_replay_for_map_input` call returns `status="failed"` with message containing `Incomplete inspection replay`.
   - Assert `reconstructed_asteroid_map_id` is `None` on failed result (matches existing incomplete path).
4. Add companion assertion: `build_initial_replay_for_map_input(..., force=True)` after trim still returns `status="ok"` with `replay_frame_count >= 6`.
5. Run `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- `django_apps/asteroid_lab/replay/event_types.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py tests/unit/asteroid_lab/test_replay_pipeline_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Regression test for trim-reconstruction scenario passes.
- [ ] `force=True` rebuild path unchanged and covered by test.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test fixture must preserve `ReconstructedAsteroidMap` row while trimming frames to reproduce the exact bug (guard checks both frame count and recon row).
- Deleting frames by event_type is safer than deleting by index to survive future frame ordering changes.
