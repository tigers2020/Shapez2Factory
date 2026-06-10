---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document canonical inspection replay frame checklist in service module

## Source Issue

- Linear: SHA-59
- Status at planning time: In Progress (moved from Todo by prior automation)
- Priority: Low

## Problem

The `_INSPECTION_EXPECTED_FRAMES` comment in `replay_pipeline_service.py` documents an outdated frame budget ("decode (1) + cleanup/reconstruction (4)") that no longer matches emitted frames, contributing to the stale guard constant.

## Scope

Update module-level documentation to list the canonical minimum inspection replay frame checklist and tie it to the completeness helper introduced in the High/Mid plans.

## Non-goals

- Changing runtime frame emission.
- Rewriting algorithm docs under `documents/Algorithm/`.
- Implementing the guard fix (covered by High/Mid plans).

## Implementation Plan

1. After High/Mid guard lands, replace the stale comment above `_INSPECTION_EXPECTED_FRAMES` with a short checklist:
   - `decode.raw_loaded`, `decode.normalized`
   - cleanup snapshots: transport, extractor, extension
   - at least one reconstruction-phase event (list canonical types or reference `event_types`)
   - minimum frame count >= 6
2. If a shared `RECONSTRUCTION_PHASE_EVENT_TYPES` frozenset is extracted for the guard, reference it in the comment to avoid drift.
3. No functional code change beyond comment/constant docstring unless the constant is renamed for clarity (e.g. `_INSPECTION_MIN_FRAMES`).

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- tests: none required (docs-only)
- manual verification: Comment matches `test_build_initial_replay_creates_run_track_frames_and_snapshots` assertions

## Acceptance Criteria

- [ ] Canonical frame checklist documented in service module comment.
- [ ] Comment no longer claims single decode frame.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Defer until guard helper exists so comment references the same event-type set used at runtime.
