---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Remove or scope invalid_x_zero guard and add integration regression

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Mid

## Problem

The replay-frame cell POST endpoint rejects valid island-local `x == 0` while the lookup service and Lab client treat column 0 as valid.

## Scope

Remove or scope the `invalid_x_zero` guard to world-map frames only (if tagging exists), and add an integration test posting `x: 0` against a `ReplayFrame` with a cell at `(0, y)`.

## Non-goals

- Do not change world-map invalid-x rules where separately tagged.
- Do not refactor coordinate-frame tagging beyond what is needed to scope the guard.

## Implementation Plan

1. Inspect `public_pages.py` lines ~722–723 for the `invalid_x_zero` guard and any coord-frame hints on the frame payload.
2. Delete the guard for island-local replay frames, or gate it only when the frame is explicitly world-map tagged.
3. Add integration test in `tests/integration/web/test_asteroid_miner_layout_solver.py` posting `x: 0` with a serialized frame containing a cell at `(0, y)`; assert 200 and expected cell detail JSON shape.
4. Run `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v -k x0` (or the new test name).

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `src/shapez2_factory/domain/asteroid_lab/coord_frames.py` (reference for IslandRawCoord)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v`
- build: n/a
- manual verification: n/a (covered by integration test)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Integration regression for `x: 0` added.
- [ ] World-map invalid-x rules unchanged if separately tagged.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Existing integration tests only exercise `x: 1`; fixture shape for `(0, y)` cells must match island bbox semantics in `replay_frame_cell_lookup`.
