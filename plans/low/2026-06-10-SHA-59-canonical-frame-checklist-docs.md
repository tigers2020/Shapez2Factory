---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: Low
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Document canonical inspection replay frame checklist in service module

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Low

## Problem

`_INSPECTION_EXPECTED_FRAMES` comment is stale relative to actual decode frame emission (two frames, not one). Future frame-count or event-type changes risk reintroducing partial-complete false positives without a documented canonical checklist.

## Scope

Add module-level comment documenting the canonical inspection replay frame and event-type checklist used by the completeness guard.

## Non-goals

- Changing frame emission counts.
- Broader replay architecture docs.
- SHA-50 overwrite semantics.

## Implementation Plan

1. After Mid plan lands completeness helper, document required frame sequence and `event_type` markers in `replay_pipeline_service.py` module comment or adjacent constant block.
2. List decode frames (`decode.raw_loaded`, `decode.normalized`), cleanup snapshots, and minimum reconstruction events.
3. Cross-reference `test_build_initial_replay_creates_run_track_frames_and_snapshots` minimum frame count assertion.
4. Note that frame-count alone is insufficient; event-type checklist is authoritative.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: N/A (docs-only within service module)
- build: N/A
- manual verification: Comment matches implemented completeness helper logic

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Canonical frame checklist documented in service module comment.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Comment must stay synchronized with completeness helper; prefer referencing helper function name over duplicating logic inline.
