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

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` via `invalid_x_zero`, but Lab replay frames and `lookup_cell_in_serialized_frame` use **island-local** coordinates where `x == 0` is valid. Users clicking cells on column 0 get HTTP 400 instead of cell detail JSON.

## Scope

Remove the erroneous `x == 0` guard from the replay-frame cell POST view so island-local `(x, y)` including `x == 0` reaches `lookup_cell_in_serialized_frame` and returns the same cell the Lab client resolves from `map_view`.

## Non-goals

- Do not change world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Do not refactor the full coordinate-frame tagging system.
- Do not change replay serialization or canvas rendering.
- Do not change Lab JS `domIndexToWorldXY` (already emits island-local `x`).

## Implementation Plan

1. Open `django_apps/web/views/public_pages.py` in `asteroid_miner_layout_replay_frame_cell` (lines 722–723).
2. Delete the guard:
   ```python
   if x == 0:
       return _bad("invalid_x_zero")
   ```
3. Confirm no other replay-frame-specific endpoint shares this guard (grep `invalid_x_zero` in `django_apps/web/`).
4. Manually verify: create a Lab project with replay bbox including `min_x == 0`, click column-0 cell, confirm POST returns `ok: true` with cell JSON (not 400).
5. Run focused integration test once Mid-priority regression is added.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py` (`asteroid_miner_layout_replay_frame_cell`)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src` (or scoped file)
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k replay_frame_cell -v` (after Mid regression added)
- build: N/A
- manual verification: Lab UI cell click on `x == 0` column returns detail modal data

## Acceptance Criteria

- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] Lab client click path works for column 0 on persisted frames.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- If world-map frames ever share this endpoint, a frame-tag gate may be needed later; current spec says replay frames are island-local only and world-map rules stay unchanged elsewhere.
