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

# Plan: Optional view unit test for x=0 replay cell POST

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Low

## Problem

No unit test directly exercises the replay-frame cell view with `x == 0` and a minimal mocked frame payload.

## Scope

Add optional view unit test using minimal mocked frame payload asserting `x: 0` returns cell detail.

## Non-goals

- Full integration test replacement (covered in Mid plan).
- Testing every coordinate permutation.

## Implementation Plan

1. Read existing view tests for `asteroid_miner_layout_replay_frame_cell` if any.
2. Add unit test with mocked `ReplayFrame` serialized payload containing cell at `(0, y)`.
3. POST `{"x": 0, "y": <y>}` to view helper or client.
4. Assert 200 and expected cell detail fields.
5. Run `pytest tests/unit/web/ -k replay_frame_cell -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_replay_frame_cell_lookup.py` (or new view test file)

## Validation Plan

- tests: `pytest tests/unit/web/ -k replay_frame_cell -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional per issue spec; skip if integration test provides sufficient coverage.
