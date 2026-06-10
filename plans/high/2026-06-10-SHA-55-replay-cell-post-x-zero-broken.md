---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix Lab cell-detail modal for island-local column x=0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: High

## Problem

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` (`invalid_x_zero`), but Lab replay frames and `lookup_cell_in_serialized_frame` use island-local coordinates where `x == 0` is valid. Users clicking cells on the `x == 0` column get HTTP 400 instead of cell detail JSON.

## Scope

Remove or scope the `x == 0` guard on the replay-frame cell POST endpoint so island-local coordinates match `lookup_cell_in_serialized_frame` and Lab client wiring.

## Non-goals

- Changing world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Refactoring the full coordinate-frame tagging system.
- Changing replay serialization or canvas rendering.

## Implementation Plan

1. Read `django_apps/web/views/public_pages.py` `asteroid_miner_layout_replay_frame_cell` (~722–723).
2. Remove `if x == 0: return _bad("invalid_x_zero")` or gate only for explicitly world-map-tagged frames (if tagging exists).
3. Confirm `lookup_cell_in_serialized_frame` already accepts `x == 0` (`tests/unit/web/test_replay_frame_cell_lookup.py`).
4. Add integration test posting `x: 0` against a `ReplayFrame` with a cell at `(0, y)`.
5. Run `pytest tests/integration/web/test_asteroid_miner_layout_solver.py tests/unit/web/test_replay_frame_cell_lookup.py -v -k x_zero` (or new test name).
6. Manual: click column 0 in Lab replay grid; cell detail modal loads.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `django_apps/web/services/replay_frame_cell_lookup.py` (reference)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (`domIndexToWorldXY` — reference)

## Validation Plan

- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v` (new x=0 case)
- lint: `ruff check django_apps/web/views/public_pages.py`
- manual verification: Lab cell click at island-local x=0 returns JSON, not 400.

## Acceptance Criteria

- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] World-map invalid-x rules unchanged (if separately tagged).
- [ ] Lab client click path works for column 0.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- If world-map frames share the same endpoint without frame tagging, removing the guard globally may allow invalid world-map x=0; verify frame coord frame metadata before blanket removal.
