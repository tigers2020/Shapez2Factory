---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Remove or scope invalid_x_zero guard on replay cell POST (SHA-55 Mid)

## Source Issue

- Linear: SHA-55
- Status at planning time: In Progress
- Priority: Mid

## Problem

View returns `_bad("invalid_x_zero")` when `x == 0` (lines 722–723 in `public_pages.py`), contradicting island-local coordinate contract and `lookup_cell_in_serialized_frame` behavior.

## Scope

Remove or replace the `x == 0` guard so island-local coordinates match lookup service and Lab client `domIndexToWorldXY` wiring. Add integration test posting `x: 0`.

## Non-goals

- Full coordinate-frame tagging refactor.
- Replay serialization or canvas rendering changes.

## Implementation Plan

1. Read `asteroid_miner_layout_replay_frame_cell` in `django_apps/web/views/public_pages.py`; locate `if x == 0: return _bad("invalid_x_zero")`.
2. Delete the guard or gate it only when the frame is explicitly world-map tagged (if tagging exists in payload); prefer deletion when endpoint is island-local only.
3. Add integration test in `tests/integration/web/test_asteroid_miner_layout_solver.py` posting `x: 0` against a `ReplayFrame` whose serialized payload includes a cell at `(0, y)`; assert 200 and expected cell JSON keys.
4. Run `pytest tests/unit/web/test_replay_frame_cell_lookup.py tests/integration/web/test_asteroid_miner_layout_solver.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `tests/unit/web/test_replay_frame_cell_lookup.py`
- `src/shapez2_factory/domain/asteroid_lab/coord_frames.py` (reference)

## Validation Plan

- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k replay -v`
- lint: `ruff check django_apps/web/views/public_pages.py`
- manual verification: Lab column-0 click

## Acceptance Criteria

- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] Integration regression for `x: 0` added.
- [ ] World-map invalid-x rules unchanged (if separately tagged).
- [ ] Lab client click path works for column 0.

## Risks / Open Questions

- If world-map and island-local share one view without tagging, document which coordinate frame the endpoint assumes.
