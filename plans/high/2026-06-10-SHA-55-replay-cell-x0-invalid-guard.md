---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fix Lab cell-detail modal for island-local column x=0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: High

## Problem

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` (`invalid_x_zero`), but Lab replay frames use island-local coordinates where `x == 0` is valid. Users clicking cells on the `x == 0` column get HTTP 400 instead of cell detail JSON.

## Scope

Remove or correctly scope the `x == 0` guard on the replay-frame cell POST endpoint so island-local coordinates match `lookup_cell_in_serialized_frame` and Lab client wiring.

## Non-goals

- World-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Full coordinate-frame tagging refactor.
- Replay serialization or canvas rendering changes.

## Implementation Plan

1. Read `asteroid_miner_layout_replay_frame_cell` in `public_pages.py` (~722–723).
2. Remove `if x == 0: return _bad("invalid_x_zero")` or gate only for explicitly world-map tagged frames.
3. Verify `lookup_cell_in_serialized_frame` already supports `x == 0`.
4. Add integration test POST with `x: 0` against frame containing cell at `(0, y)`.
5. Manual verify: Lab click on column 0 returns cell detail JSON.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `django_apps/web/services/replay_frame_cell_lookup.py` (reference)
- `tests/integration/web/test_asteroid_miner_layout_solver.py`

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps/web/views/public_pages.py`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py tests/unit/web/test_replay_frame_cell_lookup.py -v`
- build: N/A
- manual verification: Lab cell click at x=0

## Acceptance Criteria

- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] Lab client click path works for column 0.
- [ ] Matches the source issue spec.

## Risks / Open Questions

- If world-map frames share this endpoint, need explicit coord-frame tag before removing guard entirely (Mid plan).
