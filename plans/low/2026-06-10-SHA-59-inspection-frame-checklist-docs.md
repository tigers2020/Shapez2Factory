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

# Plan: Document canonical inspection replay frame checklist in service module

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Low

## Problem

The `_INSPECTION_EXPECTED_FRAMES` comment in `replay_pipeline_service.py` is stale and does not document the canonical frame sequence for a complete inspection replay. Future edits risk reintroducing count-only guards that miss reconstruction events.

## Scope

Add a module-level comment (or docstring on the completeness helper) documenting the canonical inspection replay frame checklist derived from current pipeline behavior and existing tests.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.
- External docs or ADR changes.

## Implementation Plan

1. After High/Mid implementation lands, document the canonical checklist in `replay_pipeline_service.py`:

   - Required decode events: `decode.raw_loaded`, `decode.normalized` (from `record_decoded_snapshot_frames`)
   - Required cleanup snapshot events: `replay.snapshot.cleanup_transport`, `replay.snapshot.cleanup_extractor`, `replay.snapshot.cleanup_extension` (from `record_existing_layout_inspection_frames`)
   - Required reconstruction phase: at least one of `reconstruction.begin`, `reconstruction.shell_detected`, `reconstruction.external_flood_fill`, `reconstruction.internal_void_detected`, `reconstruction.interior_patch_marked`, `reconstruction.mineable_finalized`, `reconstruction.map_complete`
   - Minimum frame count: ≥6 (2 decode + 3 cleanup + ≥1 reconstruction)

2. Cross-reference `test_build_initial_replay_creates_run_track_frames_and_snapshots` as the contract authority.
3. Note that count-only guards are insufficient; event-type checklist is required for idempotent completeness.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- tests: no new tests required (docs-only change)
- manual verification: comment matches actual frame emission in `cell_snapshot_service.py` and `existing_layout_service.py`

## Acceptance Criteria

- [ ] Canonical frame checklist documented in service module comment.
- [ ] Comment accurately reflects two decode frames (not one).
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- If reconstruction event set changes in pipeline, comment must be updated alongside tests — link to test as authority reduces drift.
