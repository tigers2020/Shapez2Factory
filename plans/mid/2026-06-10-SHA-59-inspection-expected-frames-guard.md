---
linear_issue: SHA-59
title: Inspection replay idempotency treats 5-frame partial track as complete
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix _INSPECTION_EXPECTED_FRAMES and add event-type completeness check

## Source Issue

- Linear: SHA-59
- Status at planning time: Todo
- Priority: Mid

## Problem

`_INSPECTION_EXPECTED_FRAMES = 5` comment assumes one decode frame plus four cleanup/reconstruction frames, but `record_decoded_snapshot_frames` appends two decode frames. Count-only guard is stale.

## Scope

Raise `_INSPECTION_EXPECTED_FRAMES` to documented minimum (>=6) and verify at least one reconstruction `event_type` is present before idempotent return. Add pytest for trim-reconstruction scenario.

## Non-goals

- Frame emission count changes
- SHA-50 overwrite semantics

## Implementation Plan

1. Update `_INSPECTION_EXPECTED_FRAMES` constant and module comment.
2. Add event-type checklist helper (or query reconstruction frames) before idempotent `ok` return.
3. Add pytest: build full replay, delete reconstruction frames leaving 5 frames, assert second call returns `failed` with incomplete message unless `force=True`.
4. Run `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `tests/unit/asteroid_lab/test_replay_pipeline_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/replay_pipeline_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_replay_pipeline_service.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test for trim-reconstruction scenario
- [ ] 5-frame partial track no longer returns `status="ok"` when reconstruction events missing
- [ ] Complete replays still short-circuit idempotently
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Choose between frame-count-only bump vs event-type checklist; issue recommends both.
