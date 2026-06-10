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

# Plan: Lab cell-detail modal broken for island-local column 0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: High

## Problem

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` (`invalid_x_zero`), but Lab replay frames and `lookup_cell_in_serialized_frame` use island-local coordinates where `x == 0` is valid. Users clicking cells on column 0 get HTTP 400 instead of cell detail JSON.

## Scope

Restore correct cell-detail responses for island-local `x == 0` on persisted Lab replay frames so the Lab client click path works for the leftmost column.

## Non-goals

- Do not change world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Do not refactor the full coordinate-frame tagging system.
- Do not change replay serialization or canvas rendering.

## Implementation Plan

1. Reproduce: POST `x: 0` to `asteroid_miner_layout_replay_frame_cell` with a frame containing a cell at `(0, y)`; confirm current 400 `invalid_x_zero`.
2. Remove or scope the `if x == 0: return _bad("invalid_x_zero")` guard in `django_apps/web/views/public_pages.py` so island-local frames accept `x == 0`.
3. Verify `lookup_cell_in_serialized_frame` returns the expected cell for `(0, y)` without view-layer changes beyond the guard.
4. Manually verify Lab JS `domIndexToWorldXY` click on column 0 resolves to the same coordinates the endpoint accepts.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py` (`asteroid_miner_layout_replay_frame_cell`)
- `django_apps/web/services/replay_frame_cell_lookup.py` (read-only reference)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (manual verification only)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src`
- tests: integration regression added in Mid plan
- build: n/a
- manual verification: Lab cell click on `x == 0` column returns detail JSON

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] Lab client click path works for column 0.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- If world-map frames share this endpoint without coord-frame tagging, removing the guard globally could allow invalid world-map `x == 0`. Confirm whether a world-map-only gate is required before deleting the guard.
