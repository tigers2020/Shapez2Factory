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

# Plan: Stop serving partial 5-frame inspection replays as healthy

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: High

## Problem

`build_initial_replay_for_map_input` returns `status="ok"` when `ReplayTrack.frames.count() >= 5` and a `ReconstructedAsteroidMap` exists, even if reconstruction frames were deleted. The pipeline now emits two decode frames, so five frames can mean decode + cleanup only — a permanently truncated replay.

## Scope

Fix the idempotent fast-path so partial tracks without reconstruction events never return `ok`.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose changes.

## Implementation Plan

1. Reproduce: build full replay (13 frames), delete reconstruction frames leaving 5, call `build_initial_replay_for_map_input` again → currently returns `ok`.
2. Audit `_INSPECTION_EXPECTED_FRAMES` and inline comment against actual frame emission (`decode.raw_loaded`, `decode.normalized`, cleanup, reconstruction).
3. Raise minimum frame count to >=6 and add event-type checklist (at least one reconstruction `event_type`) before idempotent return.
4. Preserve `force=True` rebuild path.
5. Verify complete replays still short-circuit without redundant work.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py` (read-only reference)
- `django_apps/asteroid_lab/services/existing_layout_service.py` (read-only reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: n/a
- manual verification: Re-import map after trimming reconstruction frames; confirm failure or rebuild, not silent `ok`.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Frame-count-only guard may drift again if pipeline adds frames; prefer event-type checklist as source of truth.
