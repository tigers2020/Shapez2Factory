---
linear_issue: SHA-59
title: Inspection replay — document canonical frame checklist
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

Service module comment describes outdated frame model (1 decode + 4 cleanup/reconstruction). Operators and future maintainers lack a single canonical checklist for inspection replay completeness.

## Scope

Document canonical frame checklist in `replay_pipeline_service.py` module comment (and optionally inline on completeness helper).

## Non-goals

- Runtime behavior changes beyond comment/docs.

## Implementation Plan

1. After mid plan lands, enumerate required `event_type` values from successful 13-frame replay test fixture.
2. Update module docstring/comment with: decode frames (`decode.raw_loaded`, `decode.normalized`), cleanup snapshots, reconstruction events minimum.
3. Cross-reference `test_build_initial_replay_creates_run_track_frames_and_snapshots` assertion `replay_frame_count >= 6`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- docs-only; no test gate beyond review

## Acceptance Criteria

- [ ] Canonical frame checklist documented in service module.
- [ ] Comment matches actual pipeline emission after mid fix.

## Risks / Open Questions

- None.
