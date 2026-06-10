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

# Plan: Remove or scope invalid_x_zero guard and add integration test

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Mid

## Problem

View returns `_bad("invalid_x_zero")` when `x == 0`; lookup service and Lab JS treat island-local `x == 0` as valid.

## Scope

Delete or scope the `invalid_x_zero` guard; add integration regression for `x: 0` POST.

## Non-goals

- World-map coord frame policy changes beyond scoping the guard.
- Canvas/replay serialization changes.

## Implementation Plan

1. Locate guard in `public_pages.py` `asteroid_miner_layout_replay_frame_cell`.
2. Delete guard or wrap: only reject `x == 0` when frame is world-map tagged (if contract exists in `coord_frames.py`).
3. Build minimal `ReplayFrame` fixture with serialized payload containing cell at `(0, y)`.
4. Add integration test:

```python
def test_replay_frame_cell_post_accepts_island_local_x_zero(client, ...):
    response = client.post(url, {"x": 0, "y": expected_y, ...})
    assert response.status_code == 200
    assert response.json()["cell_kind"] == expected_kind
```

5. Run focused pytest; ensure existing `x: 1` tests still pass.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `src/shapez2_factory/domain/asteroid_lab/coord_frames.py` (reference)

## Validation Plan

- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v`
- typecheck: `mypy django_apps/web/views/public_pages.py` (if in scope)

## Acceptance Criteria

- [ ] Integration regression for `x: 0` added.
- [ ] Guard removed or scoped to world-map only.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Integration test needs persisted frame with `(0,y)` cell in serialized JSON; reuse patterns from `test_lookup_synthetic_lab_empty_inside_island_bbox_only`.
