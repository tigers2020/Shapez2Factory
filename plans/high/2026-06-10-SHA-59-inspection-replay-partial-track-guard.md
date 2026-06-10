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

# Plan: Fix inspection replay partial-track false-complete guard

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (5) and a `ReconstructedAsteroidMap` exists. The pipeline now records two decode frames plus cleanup/reconstruction events. A 5-frame track with zero reconstruction events passes the guard and returns `status="ok"`, leaving a permanently truncated inspection replay.

## Scope

Fix the idempotent fast-path completeness guard so partial 5-frame tracks without reconstruction events are not served as healthy on re-import.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Read `replay_pipeline_service.py` idempotent return path and `_INSPECTION_EXPECTED_FRAMES` usage.
2. Raise `_INSPECTION_EXPECTED_FRAMES` to >= 6 to match `test_build_initial_replay_creates_run_track_frames_and_snapshots`.
3. Add event-type completeness check: require at least one reconstruction `event_type` before idempotent `ok` return (or canonical frame checklist helper).
4. Ensure `force=True` rebuild path bypasses guard unchanged.
5. Verify complete replays (13+ frames with reconstruction) still short-circuit idempotently.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (context only)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (context only)
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing.
- [ ] Complete replays still short-circuit idempotently.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Exact minimum frame count vs event-type checklist: prefer both for defense in depth.
- Related SHA-50 stale cache bug is distinct; do not conflate fixes.
