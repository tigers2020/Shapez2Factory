---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete (stale _INSPECTION_EXPECTED_FRAMES)
priority: High
labels:
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Stop serving partial 5-frame inspection replay as healthy

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (currently `5`) and a `ReconstructedAsteroidMap` row exists. The constant assumes one decode frame plus four cleanup/reconstruction frames, but the pipeline now records two decode frames (`decode.raw_loaded`, `decode.normalized`). A track with only decode + three cleanup frames (five total, zero reconstruction events) passes the guard and returns `status="ok"`, leaving a permanently truncated inspection replay.

## Scope

Fix the inspection replay completeness guard so partial 5-frame tracks without reconstruction events no longer return `status="ok"`.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Reproduce: build full replay (13 frames), delete reconstruction frames leaving 5 (`decode.raw_loaded`, `decode.normalized`, three cleanup); second `build_initial_replay_for_map_input` returns `status="ok"` with `replay_frame_count=5`.
2. Raise `_INSPECTION_EXPECTED_FRAMES` to documented minimum (>=6) and/or add event-type completeness checklist before idempotent return.
3. Require at least one reconstruction `event_type` (or canonical frame checklist) in addition to frame count.
4. Verify complete replays still short-circuit idempotently.
5. Confirm `force=True` rebuild path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (reference)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: N/A
- manual verification: Trim-reconstruction scenario returns failed/incomplete on second call without `force=True`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing.
- [ ] Complete replays still short-circuit idempotently.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Event-type checklist vs frame-count-only guard: prefer checklist to survive future frame-count changes.
