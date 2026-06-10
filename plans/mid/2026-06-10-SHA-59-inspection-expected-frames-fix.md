---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Mid
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Fix _INSPECTION_EXPECTED_FRAMES and event-type completeness checklist

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment states "decode (1) + cleanup/reconstruction (4)" but `record_decoded_snapshot_frames` appends two decode frames. Frame-count-only guard is stale; idempotent fast-path must validate required `event_type` markers or a canonical frame checklist.

## Scope

Update `replay_pipeline_service.py` completeness guard (constant and/or event-type checklist) and add pytest for trim-reconstruction scenario.

## Non-goals

- Decode/cleanup/reconstruction emission count changes.
- SHA-50 overwrite semantics.
- Timeline compose pipeline changes.

## Implementation Plan

1. Update `_INSPECTION_EXPECTED_FRAMES` to >=6 aligned with `test_build_initial_replay_creates_run_track_frames_and_snapshots`.
2. Add helper (e.g. `_inspection_replay_is_complete(track)`) checking required `event_type` markers including reconstruction events.
3. Gate idempotent return in `build_initial_replay_for_map_input` on helper result, not frame count alone.
4. Add pytest: build full replay, trim reconstruction frames to five, assert second call returns `failed` with existing incomplete message unless `force=True`.
5. Assert complete replay second call still returns `status="ok"`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: N/A
- manual verification: Trim scenario fails; full replay idempotency passes

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Constant and/or event-type checklist fixed.
- [ ] Regression test for trim-reconstruction scenario added.
- [ ] `force=True` rebuild path unchanged.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Canonical event types must match `record_decoded_snapshot_frames` and reconstruction emitters; verify against live pipeline before locking checklist.
