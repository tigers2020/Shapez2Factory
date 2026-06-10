---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Replay cell view unit test for x=0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Low

## Problem

Optional view unit test with mocked frame payload.

## Scope

Add a focused unit test on `asteroid_miner_layout_replay_frame_cell` using a minimal mocked `ReplayFrame` payload asserting `x: 0` returns cell detail JSON.

## Non-goals

- Do not change world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Do not refactor the full coordinate-frame tagging system.
- Do not change replay serialization or canvas rendering.

## Implementation Plan

1. Create or extend view unit test module for `public_pages.py` replay-frame cell endpoint.
2. Mock a `ReplayFrame` with serialized payload containing a cell at island-local `(0, y)`.
3. POST `{ x: 0, y: <valid> }` and assert 200 with expected cell detail JSON.
4. Assert `invalid_x_zero` is not returned for island-local frames.

## Files / Areas Likely Affected

- `tests/unit/web/test_replay_frame_cell_lookup.py` (or new view unit test module)
- `django_apps/web/views/public_pages.py` (test target only)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_replay_frame_cell_lookup.py -v` (or new test path once added)
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High/Mid guard removal landing first.
- Integration test in Mid plan may suffice; this is optional coverage.
