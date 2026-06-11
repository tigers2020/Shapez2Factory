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

# Plan: Lab cell-detail modal for island-local column x=0

## Source Issue

- Linear: SHA-55
- Status at planning time: In Progress
- Priority: High

## Problem

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` via `invalid_x_zero`, but Lab replay frames and `lookup_cell_in_serialized_frame` use island-local coordinates where `x == 0` is valid. Users clicking cells on column 0 get HTTP 400 instead of cell detail JSON.

## Scope

Restore end-to-end Lab cell-detail behavior for island-local `x == 0` by aligning the replay-frame cell POST endpoint with the lookup service and Lab client coordinate mapping (`domIndexToWorldXY`).

## Non-goals

- Do not change world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Do not refactor the full coordinate-frame tagging system.
- Do not change replay serialization or canvas rendering.

## Implementation Plan

1. Remove the `if x == 0: return _bad("invalid_x_zero")` guard in `asteroid_miner_layout_replay_frame_cell` (`django_apps/web/views/public_pages.py` lines 722–723).
2. Confirm the view docstring still describes island-local coords (update comment if it still says "world").
3. Manually verify Lab click on column 0 returns cell JSON when replay bbox includes `minD` such that `x == 0` is in range.
4. Run focused integration test once Mid plan adds `x: 0` regression.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py` (`asteroid_miner_layout_replay_frame_cell`)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (`domIndexToWorldXY` — verify only, no change expected)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py::test_replay_frame_cell_post_returns_cell_json -v` (baseline) plus new `x: 0` test from Mid plan
- build: `python manage.py check`
- manual verification: Lab replay frame with bbox including column 0 — click cell, confirm modal/detail JSON loads (no 400)

## Acceptance Criteria

- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] Lab client click path works for column 0.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- View docstring says "world (x, y)" but endpoint is island-local; clarify in comment only (no contract refactor).
- If any caller relied on `invalid_x_zero` as a world-map guard, confirm no such caller exists before delete (issue spec says world-map rules unchanged elsewhere).
