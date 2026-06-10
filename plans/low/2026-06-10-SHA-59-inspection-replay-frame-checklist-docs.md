---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Low
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Document canonical inspection replay frame checklist

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Low

## Problem

Service module comment for `_INSPECTION_EXPECTED_FRAMES` is stale ("decode (1) + cleanup/reconstruction (4)") and does not document the canonical frame/event checklist operators should expect.

## Scope

Document canonical frame checklist in `replay_pipeline_service.py` module comment.

## Non-goals

- External user-facing documentation.
- Changing frame emission pipeline.

## Implementation Plan

1. After Mid plan fixes guard, update module comment near `_INSPECTION_EXPECTED_FRAMES`.
2. List expected decode frames (`decode.raw_loaded`, `decode.normalized`), cleanup snapshots, and reconstruction event types.
3. Cross-reference `test_build_initial_replay_creates_run_track_frames_and_snapshots` minimum frame count.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Docs-only; depends on Mid plan landing first for accurate checklist values.
