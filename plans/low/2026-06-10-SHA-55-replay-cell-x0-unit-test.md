---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Optional view unit test for x=0 cell POST

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Low

## Problem

Integration test covers the full path; optional view-level unit test with mocked frame payload gives faster feedback on guard removal.

## Scope

Optional unit test on `asteroid_miner_layout_replay_frame_cell` using minimal mocked serialized frame with cell at `(0, y)`.

## Non-goals

- Replacing integration test (Mid plan owns primary regression).

## Implementation Plan

1. Add `test_replay_frame_cell_accepts_island_local_x_zero` in `tests/unit/web/test_replay_frame_cell_lookup.py` or new view test module.
2. Mock frame lookup to return payload with cell at x=0.
3. POST to view; assert not 400 `invalid_x_zero`.
4. Run: `pytest tests/unit/web/ -v -k x_zero`.

## Files / Areas Likely Affected

- `tests/unit/web/test_replay_frame_cell_lookup.py` or new view test file

## Validation Plan

- tests: targeted pytest

## Acceptance Criteria

- [ ] Optional view unit test added if integration test insufficient.
- [ ] Matches the source issue spec.

## Risks / Open Questions

- Defer if Mid integration test provides adequate coverage.
