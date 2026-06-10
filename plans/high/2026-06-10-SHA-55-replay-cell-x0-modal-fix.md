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

# Plan: Fix Lab cell-detail modal for island-local column 0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: High

## Problem

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` (`invalid_x_zero`), but Lab replay frames use island-local coordinates where `x == 0` is valid. Users clicking cells on the `x == 0` column get HTTP 400 instead of cell detail JSON.

## Scope

Fix the replay-frame cell POST endpoint so island-local `x == 0` returns cell detail JSON, restoring Lab cell-detail modal for column 0.

## Non-goals

- Changing world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Refactoring the full coordinate-frame tagging system.
- Changing replay serialization or canvas rendering.

## Implementation Plan

1. Read `asteroid_miner_layout_replay_frame_cell` in `django_apps/web/views/public_pages.py` (lines 722–723).
2. Remove or scope the `if x == 0: return _bad("invalid_x_zero")` guard to world-map frames only.
3. Verify `lookup_cell_in_serialized_frame` already supports `x == 0`.
4. Confirm Lab JS `domIndexToWorldXY` click path yields `x == 0` for valid bbox column 0.
5. Manually test cell click on column 0 returns detail JSON.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `django_apps/web/services/replay_frame_cell_lookup.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v`
- build: `python manage.py check`
- manual verification: Lab cell click on column 0 opens detail modal

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- If world-map and island-local frames share the same endpoint without tagging, scoping the guard requires frame-type detection.
