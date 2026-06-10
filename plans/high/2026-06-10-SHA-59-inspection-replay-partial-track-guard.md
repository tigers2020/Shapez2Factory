---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: High
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Stop serving partial 5-frame inspection replay as healthy on re-import

## Source Issue

- Linear: SHA-59
- Status at planning time: In Progress (moved from Todo by prior automation)
- Priority: High

## Problem

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (currently `5`) and a `ReconstructedAsteroidMap` row exists. The constant and comment assume one decode frame plus four cleanup/reconstruction frames, but the pipeline now records two decode frames (`decode.raw_loaded`, `decode.normalized`) and at least one reconstruction event. A track with only decode plus three cleanup frames (five total, zero reconstruction events) passes the guard and returns `status="ok"`, leaving a permanently truncated inspection replay.

## Scope

Fix the idempotent fast-path completeness guard in `replay_pipeline_service.py` so partial tracks with missing reconstruction events never return `status="ok"`.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Read the idempotent branch in `build_initial_replay_for_map_input` (lines ~128–163) and the existing happy-path test event-type assertions in `test_replay_pipeline_service.py`.
2. Introduce a helper (e.g. `_inspection_replay_is_complete(track)`) that returns `False` unless:
   - frame count is at least the documented minimum (>= 6), **and**
   - at least one reconstruction-phase `event_type` is present (reuse `recon_phase_types` frozenset from tests or import from `event_types`).
3. Raise `_INSPECTION_EXPECTED_FRAMES` from `5` to `6` and update the module comment to reflect two decode frames plus cleanup/reconstruction.
4. Replace the `n >= _INSPECTION_EXPECTED_FRAMES` check with the helper so a 5-frame partial track with `ReconstructedAsteroidMap` still fails with the existing incomplete message.
5. Confirm complete replays (>= 6 frames with reconstruction events) still short-circuit idempotently without rebuild.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/replay/event_types.py` (if canonical reconstruction event list is centralized)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- manual verification: Build full replay, delete reconstruction frames leaving 5 decode+cleanup frames, second call returns `status="failed"` not `ok`

## Acceptance Criteria

- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing.
- [ ] Complete replays still short-circuit idempotently.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Stale `ReconstructedAsteroidMap` row may still exist when guard rejects partial track; confirm `reconstructed_asteroid_map_id` handling in failed DTO matches existing incomplete-path behavior.
- Event-type checklist must stay aligned with `record_existing_layout_inspection_frames` emission; prefer shared constant over duplicated frozenset.
