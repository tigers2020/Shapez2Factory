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

# Plan: Scope invalid_x_zero removal and add x=0 integration regression

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Mid

## Problem

The replay-frame cell POST view rejects `x == 0` while the lookup service and unit tests (`test_lookup_synthetic_lab_empty_inside_island_bbox_only`) already treat island-local `x == 0` as valid. Integration coverage only exercises `x: 1`.

## Scope

1. Remove or scope the `invalid_x_zero` guard so it does not apply to island-local replay-frame lookups.
2. Add integration regression posting `x: 0` against a `ReplayFrame` whose serialized payload includes a cell at `(0, y)`.

## Non-goals

- Do not change world-map invalid-x rules on other endpoints.
- Do not refactor coordinate-frame tagging.
- Do not change replay serialization.

## Implementation Plan

1. After High-priority guard removal in `public_pages.py`, grep repo for `invalid_x_zero` and confirm no stale references remain in replay path.
2. In `tests/integration/web/test_asteroid_miner_layout_solver.py`, add `test_replay_frame_cell_post_accepts_island_local_x_zero`:
   - Create project via existing `_unique_valid_copy()` + create URL helper pattern from `test_replay_frame_cell_post_returns_cell_json`.
   - Load first `ReplayFrame`; if bbox lacks `min_x == 0`, use a synthetic serialized frame fixture or seed frame with `full_map` entry at `(0, y)` per `test_lookup_synthetic_lab_empty_inside_island_bbox_only` pattern.
   - POST body: `x: 0`, `y: 0` (or known cell y), plus `replay_frame_id`, `replay_track_id`, `project_slug`.
   - Assert `response.status_code == 200`, `data["ok"] is True`, and cell JSON present when frame has cell at `(0, y)`.
3. Optionally assert `invalid_x_zero` is not returned for `x: 0` (error message absent).
4. Run: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k replay_frame_cell -v`.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `django_apps/web/services/replay_frame_cell_lookup.py` (reference only; already supports x=0)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -k replay_frame_cell -v`
- build: N/A
- manual verification: N/A if integration test covers x=0 path

## Acceptance Criteria

- [ ] `invalid_x_zero` guard removed or scoped away from island-local replay frames.
- [ ] Integration regression for `x: 0` POST added and passing.
- [ ] World-map invalid-x rules unchanged on other endpoints.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Default solver-created frames may not include a cell at `(0, 0)`; test may need explicit `full_map` seed in frame payload or use `message: no_cell_at_xy` with `ok: true` to prove guard removal without requiring occupied cell.
