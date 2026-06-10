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

`_INSPECTION_EXPECTED_FRAMES` comment is stale relative to actual decode/cleanup/reconstruction emission. Future pipeline changes risk reintroducing false-complete idempotency without a documented canonical frame checklist.

## Scope

Add module-level comment (or short docstring on completeness helper) listing required inspection replay frame stages and `event_type` markers used by the idempotent guard.

## Non-goals

- Do not change runtime behavior (covered by High/Mid plans).
- Do not add external docs files unless team convention requires.

## Implementation Plan

1. After Mid guard fix, document in `replay_pipeline_service.py`:
   - Decode frames: `decode.raw_loaded`, `decode.normalized`
   - Cleanup snapshot stages (names from `existing_layout_service`)
   - Minimum reconstruction `event_type`(s) required for complete replay
   - Minimum frame count used by guard
2. Cross-reference `test_build_initial_replay_creates_run_track_frames_and_snapshots` assertion (`>= 6`).
3. No code behavior change unless comment reveals mismatch needing one-line constant fix.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: N/A
- tests: N/A (docs-only)
- build: N/A
- manual verification: Comment matches emitted frame types in services

## Acceptance Criteria

- [ ] Canonical frame checklist documented in service module.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Checklist must stay in sync with pipeline emitters; consider linking to test name in comment only.
