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

# Plan: Optional view unit test for x=0 replay cell POST (SHA-55 Low)

## Source Issue

- Linear: SHA-55
- Status at planning time: In Progress
- Priority: Low

## Problem

Integration coverage for `x: 0` may be sufficient; a minimal view unit test with mocked frame payload can catch guard regressions faster than full layout solver integration.

## Scope

Optionally add a unit test on `asteroid_miner_layout_replay_frame_cell` using a minimal mocked `ReplayFrame` serialized payload with a cell at `(0, y)`.

## Non-goals

- Replacing integration regression from Mid plan.

## Implementation Plan

1. If integration test in Mid plan is heavy, add `tests/unit/web/test_replay_frame_cell_view.py` (or extend existing web view tests) with Django request factory POST `{"x": 0, "y": <y>}` against mocked frame.
2. Assert 200 response and cell detail fields match `lookup_cell_in_serialized_frame` output.
3. Run `pytest tests/unit/web/ -k replay_frame_cell -v`.

## Files / Areas Likely Affected

- `tests/unit/web/` (new or extended test module)
- `django_apps/web/views/public_pages.py`

## Validation Plan

- tests: new unit test green alongside integration test

## Acceptance Criteria

- [ ] Optional unit test added or explicitly deferred with reason in PR.
- [ ] Stays within Low scope.

## Risks / Open Questions

- Mock fidelity must include `map_view` shape the lookup service expects.
