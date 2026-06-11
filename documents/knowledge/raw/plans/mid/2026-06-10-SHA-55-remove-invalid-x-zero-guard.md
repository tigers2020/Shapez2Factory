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

# Plan: Remove invalid_x_zero guard and add x=0 integration regression

## Source Issue

- Linear: SHA-55
- Status at planning time: In Progress
- Priority: Mid

## Problem

The replay-frame cell POST view rejects `x == 0` before lookup runs, while `lookup_cell_in_serialized_frame` already supports island-local `x == 0` (see `test_lookup_synthetic_lab_empty_inside_island_bbox_only`). Integration tests only exercise `x: 1`.

## Scope

Delete or correctly scope the `invalid_x_zero` guard and add an integration regression that POSTs `x: 0` against a persisted `ReplayFrame` whose serialized payload includes or synthesizes a cell at `(0, y)`.

## Non-goals

- Do not change world-map invalid-x rules on other endpoints.
- Do not refactor coordinate-frame tagging.
- Do not change replay serialization.

## Implementation Plan

1. Delete `if x == 0: return _bad("invalid_x_zero")` in `asteroid_miner_layout_replay_frame_cell` unless frame tagging explicitly requires world-map scoping (issue evidence: no such tagging on this endpoint today).
2. Add `test_replay_frame_cell_post_accepts_island_local_x_zero` in `tests/integration/web/test_asteroid_miner_layout_solver.py`:
   - Create project via existing `_unique_valid_copy()` helper.
   - Pick first `ReplayFrame`; if bbox does not include `x == 0`, use a frame/fixture with `summary.bbox` spanning `min_x <= 0` or seed `full_map` cell at `(0, 0)`.
   - POST with `"x": 0`, `"y": 0` (or known in-bbox y).
   - Assert HTTP 200, `ok: true`, and cell JSON (or `message: no_cell_at_xy` only if fixture has no cell — prefer fixture with resolvable cell).
3. Run `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k replay_frame_cell -v`.
4. Grep repo for `invalid_x_zero` to confirm no stale references remain.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `django_apps/web/services/replay_frame_cell_lookup.py` (read-only reference)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py tests/integration/web/test_asteroid_miner_layout_solver.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k replay_frame_cell -v`
- build: `python manage.py check`
- manual verification: optional — confirm existing `x: 1` tests still pass unchanged

## Acceptance Criteria

- [ ] `invalid_x_zero` guard removed or scoped only to world-map frames (if tagging exists).
- [ ] Integration regression for `x: 0` POST added.
- [ ] World-map invalid-x rules unchanged on other endpoints.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Default `_unique_valid_copy()` frame may not have a physical cell at `(0,0)`; test may assert synthetic `lab_empty` via bbox — align assertion with `lookup_cell_in_serialized_frame` behavior.
- Confirm no separate world-map cell POST endpoint shares this guard pattern.
