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

# Plan: Document canonical inspection frame checklist

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Low

## Problem

Module comment on `_INSPECTION_EXPECTED_FRAMES` is stale (assumes one decode frame). Future drift risk without documented canonical frame sequence.

## Scope

Update `replay_pipeline_service.py` module comment to list expected frame groups and event markers used by completeness guard.

## Non-goals

- Runtime behavior changes beyond comment/helper docstrings.

## Implementation Plan

1. After Mid plan implements helper, document in module header:
   - decode frames: `decode.raw_loaded`, `decode.normalized`
   - cleanup snapshot frames (count/source)
   - reconstruction event types required for completeness
2. Cross-link to `test_build_initial_replay_creates_run_track_frames_and_snapshots` minimum frame assertion.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py` (comments only)

## Validation Plan

- docs-only; no test gate required beyond review

## Acceptance Criteria

- [ ] Comment reflects current pipeline frame budget.
- [ ] Checklist matches helper logic from Mid plan.

## Risks / Open Questions

- None.
