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

# Plan: Document canonical inspection replay frame checklist

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Low

## Problem

Service comment still says "decode (1) + cleanup/reconstruction (4)" while pipeline emits two decode frames.

## Scope

Update module comment (and optionally a small docstring on the completeness helper) with the canonical frame/event checklist.

## Non-goals

- Runtime behavior changes (covered in Mid/High plans).

## Implementation Plan

1. After Mid helper lands, document required `event_type` values and minimum frame count in `replay_pipeline_service.py`.
2. Cross-link to `test_build_initial_replay_creates_run_track_frames_and_snapshots` assertion (`replay_frame_count >= 6`).
3. Remove stale "decode (1)" wording.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: n/a
- tests: n/a
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Docs-only; land with or after Mid implementation.
