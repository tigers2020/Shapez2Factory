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

The `invalid_x_zero` guard is applied unconditionally on the replay-frame cell POST endpoint. Integration tests only exercise `x: 1`, leaving the `x == 0` island-local path unguarded by regression.

## Scope

Remove or scope `invalid_x_zero` guard to world-map frames only; add integration test posting `x: 0` against a frame with a cell at `(0, y)`.

## Non-goals

- Changing `IslandRawCoord` domain rules.
- Adding world-map frame tagging system beyond what exists today.

## Implementation Plan

1. Determine whether frame payloads expose coordinate-frame tagging (check `coord_frames.py`, serialized frame schema).
2. If tagging exists, gate `invalid_x_zero` on world-map frames only; else remove guard for replay endpoint.
3. Add integration test in `tests/integration/web/test_asteroid_miner_layout_solver.py` posting `x: 0`.
4. Seed `ReplayFrame` with serialized payload containing cell at `(0, y)`.
5. Assert HTTP 200 and cell detail JSON returned.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `src/shapez2_factory/domain/asteroid_lab/coord_frames.py`

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py tests/integration/web/test_asteroid_miner_layout_solver.py`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- World-map invalid-x rules must remain unchanged if separately tagged; confirm no regression on world-map paths.
