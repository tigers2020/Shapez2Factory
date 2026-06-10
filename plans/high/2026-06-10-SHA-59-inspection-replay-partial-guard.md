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

`build_initial_replay_for_map_input` short-circuits as complete when `ReplayTrack.frames.count() >= _INSPECTION_EXPECTED_FRAMES` (5) and a `ReconstructedAsteroidMap` row exists. The pipeline now records two decode frames, so a 5-frame partial track with zero reconstruction events passes the guard and returns `status="ok"`.

## Scope

Fix the inspection replay completeness guard so partial 5-frame tracks no longer return healthy status on re-import.

## Non-goals

- Changing decode/cleanup/reconstruction frame emission counts.
- Reworking `resolve_inspection_solver_run` overwrite semantics (SHA-50).
- Broader replay timeline compose or artifact ingest changes.

## Implementation Plan

1. Read `_INSPECTION_EXPECTED_FRAMES` and idempotent short-circuit in `replay_pipeline_service.py`.
2. Reproduce: build full replay, delete reconstruction frames leaving 5, second call returns `ok` (confirms bug).
3. Raise `_INSPECTION_EXPECTED_FRAMES` to >= 6 and/or add reconstruction `event_type` checklist.
4. Ensure complete replays still short-circuit idempotently.
5. Verify `force=True` rebuild path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Frame-count-only guard may drift again if pipeline adds frames; event-type checklist is more durable.
