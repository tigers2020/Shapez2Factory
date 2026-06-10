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

# Plan: Stop serving partial 5-frame inspection replay as healthy

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` idempotent fast-path treats `ReplayTrack.frames.count() >= 5` plus an existing `ReconstructedAsteroidMap` as complete. The pipeline now emits two decode frames (`decode.raw_loaded`, `decode.normalized`), so five frames can mean decode + cleanup only with zero reconstruction events. Re-import then returns `status="ok"` with a permanently truncated replay.

## Scope

Fix the completeness guard so partial tracks without reconstruction events cannot short-circuit as `ok`.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Read `django_apps/asteroid_lab/services/replay_pipeline_service.py` idempotent branch (~lines 130–145).
2. Raise `_INSPECTION_EXPECTED_FRAMES` from `5` to `>= 6` to match `test_build_initial_replay_creates_run_track_frames_and_snapshots`.
3. Add reconstruction `event_type` presence check (at least one reconstruction marker) before returning `ok` on idempotent path.
4. When guard fails, return existing `failed` incomplete message or rebuild per current contract (do not change `force=True` path).
5. Manual repro: full replay → delete reconstruction frames leaving 5 → second call must not return `ok`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (frame event types reference)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (reconstruction frames reference)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps/asteroid_lab/services/replay_pipeline_service.py`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing.
- [ ] Complete replays still short-circuit idempotently.
- [ ] Stays within the priority scope.
- [ ] `force=True` rebuild path unchanged.

## Risks / Open Questions

- Event-type checklist must stay aligned if pipeline adds frames; prefer marker check over brittle exact count if frame budget shifts again.
