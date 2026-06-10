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

# Plan: Stop serving partial 5-frame inspection replay as healthy

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (5) and a `ReconstructedAsteroidMap` exists. The pipeline now records two decode frames plus cleanup/reconstruction events; a 5-frame track with zero reconstruction events incorrectly returns `status="ok"`, leaving a permanently truncated inspection replay.

## Scope

Fix the inspection replay completeness guard so partial tracks missing reconstruction events no longer return `ok` on re-import.

## Non-goals

- Do not change decode/cleanup/reconstruction frame emission counts.
- Do not rework `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Do not change broader replay timeline compose or artifact ingest.

## Implementation Plan

1. Open `django_apps/asteroid_lab/services/replay_pipeline_service.py` and locate idempotent fast-path using `_INSPECTION_EXPECTED_FRAMES`.
2. Raise minimum frame count to >= 6 to match `test_build_initial_replay_creates_run_track_frames_and_snapshots`.
3. Add event-type completeness check: require at least one reconstruction `event_type` before returning `ok` (or use canonical frame checklist helper).
4. Ensure incomplete tracks return existing `failed` message unless `force=True`.
5. Verify complete replays still short-circuit idempotently.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v` (after Mid regression added)
- build: N/A
- manual verification: Re-import after trimming reconstruction frames should not return `ok`

## Acceptance Criteria

- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing.
- [ ] Complete replays still short-circuit idempotently.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Exact reconstruction `event_type` strings must match production frame payloads; confirm against `existing_layout_service` / `cell_snapshot_service` emitters.
