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

# Plan: Scope invalid_x_zero guard and add integration test

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Mid

## Problem

The view applies a blanket `x == 0` rejection that predates island-local replay coordinates. Lookup service and Lab JS already treat `x == 0` as valid island-local.

## Scope

Remove or scope `invalid_x_zero` guard to world-map frames only. Add integration test for `x: 0` POST.

## Non-goals

- Coordinate-frame tagging system refactor.

## Implementation Plan

1. Inspect whether replay frame payload exposes coord-frame tag (`IslandRawCoord` vs world-map).
2. If tagged: guard `invalid_x_zero` only for world-map frames.
3. If untagged (current state): delete guard — replay frames are island-local per `coord_frames.py` and research doc.
4. Add integration test in `test_asteroid_miner_layout_solver.py`:
   - Seed `ReplayFrame` with cell at `(0, y)` in serialized payload.
   - POST `{x: 0, y: ...}` to cell endpoint.
   - Assert 200 + cell detail JSON.
5. Run: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v -k replay_frame_cell`.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `src/shapez2_factory/domain/asteroid_lab/coord_frames.py` (reference)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v`
- manual verification: column 0 click in Lab

## Acceptance Criteria

- [ ] Integration regression for `x: 0` added.
- [ ] World-map invalid-x rules unchanged if separately tagged.
- [ ] Matches the source issue spec.

## Risks / Open Questions

- Integration test fixture must include island-local cell at x=0 in frame JSON.
