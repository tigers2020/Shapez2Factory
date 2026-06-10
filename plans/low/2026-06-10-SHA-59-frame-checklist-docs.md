---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document canonical inspection replay frame checklist

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Low

## Problem

Service module comment for `_INSPECTION_EXPECTED_FRAMES` is stale and does not document the canonical frame/event checklist operators and tests should expect.

## Scope

Document canonical frame checklist in `replay_pipeline_service.py` module comment after guard fix.

## Non-goals

- Changing frame emission logic
- New runtime behavior

## Implementation Plan

1. After Mid plan guard fix, update module-level comment near `_INSPECTION_EXPECTED_FRAMES`.
2. List required decode, cleanup, and reconstruction event types.
3. Cross-reference `test_build_initial_replay_creates_run_track_frames_and_snapshots`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: N/A (comment only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Comment matches implemented guard

## Acceptance Criteria

- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- None.
