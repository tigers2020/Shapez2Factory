---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete
priority: High
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix partial 5-frame inspection replay served as healthy

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (5) and a `ReconstructedAsteroidMap` exists. The pipeline now records two decode frames, so a 5-frame track with zero reconstruction events incorrectly returns `status="ok"`, leaving a permanently truncated inspection replay.

## Scope

Fix the inspection replay completeness guard so partial tracks without reconstruction events are not served as healthy on re-import.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50)
- Broader replay timeline compose or artifact ingest changes

## Implementation Plan

1. Read `django_apps/asteroid_lab/services/replay_pipeline_service.py` and `_INSPECTION_EXPECTED_FRAMES`.
2. Identify idempotent fast-path guard (frame count + reconstructed map check).
3. Raise minimum frame count to >=6 and/or require reconstruction `event_type` presence.
4. Ensure complete replays still short-circuit idempotently.
5. Verify `force=True` rebuild path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (read-only)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (read-only)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: N/A
- manual verification: Re-import after trimming reconstruction frames fails without `force=True`

## Acceptance Criteria

- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing
- [ ] Complete replays still short-circuit idempotently
- [ ] `force=True` rebuild path unchanged
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Exact canonical frame checklist should align with `test_build_initial_replay_creates_run_track_frames_and_snapshots` (>=6 frames).
