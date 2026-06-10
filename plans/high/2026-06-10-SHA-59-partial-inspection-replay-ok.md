---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: High
labels:
  - bug
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Stop serving partial 5-frame inspection replay as healthy on re-import

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (currently `5`) and a `ReconstructedAsteroidMap` row exists. The pipeline now records two decode frames (`decode.raw_loaded`, `decode.normalized`) plus cleanup and reconstruction events. A track with only decode + three cleanup frames (five total, zero reconstruction `event_type` markers) passes the guard and returns `status="ok"`, leaving a permanently truncated inspection replay on re-import.

## Scope

Tighten the idempotent fast-path in `replay_pipeline_service.py` so partial inspection replays missing reconstruction events never return `status="ok"`. Preserve existing `failed` messaging for incomplete tracks (`"Incomplete inspection replay; pass force=True to rebuild."`).

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Read the fast-path guard at lines 128–143 in `django_apps/asteroid_lab/services/replay_pipeline_service.py` (`n >= _INSPECTION_EXPECTED_FRAMES` + `recon_pk`).
2. Extract a helper (e.g. `_inspection_replay_is_complete(track) -> bool`) that returns `False` when reconstruction `event_type` markers are absent, even if frame count ≥ 5.
3. Reuse the reconstruction phase set already asserted in `test_build_initial_replay_creates_run_track_frames_and_snapshots` (`reconstruction.begin`, `reconstruction.shell_detected`, etc.) or import from `django_apps/asteroid_lab/replay/event_types.py`.
4. Replace the count-only guard with `n >= _INSPECTION_EXPECTED_FRAMES and _inspection_replay_is_complete(track) and recon_pk is not None`.
5. Manually repro: build full replay (≥13 frames), delete reconstruction frames leaving 5 decode+cleanup frames, call `build_initial_replay_for_map_input` again — must return `status="failed"`, not `ok`.
6. Confirm complete replays (≥6 frames with reconstruction events) still short-circuit idempotently.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/replay/event_types.py` (read-only reference for reconstruction event constants)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps/asteroid_lab/services/replay_pipeline_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- manual verification: trim-reconstruction repro from issue spec

## Acceptance Criteria

- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Stale `ReconstructedAsteroidMap` row may still exist while replay is incomplete; guard must not treat map row alone as completeness signal.
- Related SHA-50 overwrite stale SolverRun cache is a separate bug.
