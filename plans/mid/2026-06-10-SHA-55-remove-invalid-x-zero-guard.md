---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Remove invalid_x_zero guard + integration test

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Mid

## Problem

Remove or scope `invalid_x_zero` guard to world-map frames only; integration test for `x: 0` POST.

## Scope

Delete the blanket `x == 0` rejection on the replay-frame cell POST endpoint and add an integration regression posting `x: 0` against a `ReplayFrame` with a cell at `(0, y)`.

## Non-goals

- Do not change world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Do not refactor the full coordinate-frame tagging system.
- Do not change replay serialization or canvas rendering.

## Implementation Plan

1. Delete `if x == 0: return _bad("invalid_x_zero")` in `asteroid_miner_layout_replay_frame_cell` (or gate only when frame is explicitly world-map tagged).
2. Add integration test to `tests/integration/web/test_asteroid_miner_layout_solver.py` posting `x: 0` with serialized payload containing a cell at `(0, y)`.
3. Assert 200 response with cell detail JSON matching `lookup_cell_in_serialized_frame` output.
4. Confirm existing tests exercising `x: 1` still pass.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `django_apps/web/services/replay_frame_cell_lookup.py`
- `tests/integration/web/test_asteroid_miner_layout_solver.py`
- `tests/unit/web/test_replay_frame_cell_lookup.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v`
- build: `python manage.py check`
- manual verification: Lab click on column 0 returns cell detail

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlaps High plan — implement together in one PR if practical.
- Low plan adds optional view unit test with mocked frame payload.
