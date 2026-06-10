---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional view unit test with mocked frame payload

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Low

## Problem

Integration test covers end-to-end path; optional faster unit test on the view with minimal mocked frame can guard regression without DB fixture weight.

## Scope

Optional unit test on `asteroid_miner_layout_replay_frame_cell` using mocked `ReplayFrame` and serialized payload with `x == 0` cell.

## Non-goals

- Replacing integration test (Mid plan).
- Changing lookup service.

## Implementation Plan

1. Add `tests/unit/web/test_replay_frame_cell_view.py` (or extend existing view tests if present).
2. Mock `ReplayFrame` queryset / frame loader to return minimal serialized frame with cell at `(0, y)`.
3. POST `x=0, y=...` to view; assert 200 and cell detail keys.
4. Run `pytest tests/unit/web/test_replay_frame_cell_view.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_replay_frame_cell_view.py` (new, optional)
- `django_apps/web/views/public_pages.py` (under test)

## Validation Plan

- tests: `pytest tests/unit/web/test_replay_frame_cell_view.py -v`

## Acceptance Criteria

- [ ] Optional unit test passes if implemented.
- [ ] Does not duplicate integration coverage redundantly.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- May be skipped if integration test (Mid) provides sufficient coverage; Low priority is explicitly optional per issue spec.
