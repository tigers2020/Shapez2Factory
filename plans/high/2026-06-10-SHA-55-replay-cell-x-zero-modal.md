---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Fix replay cell modal for column 0

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: High

## Problem

Lab cell-detail modal broken for valid island-local column 0 on persisted frames.

## Scope

Restore POST acceptance of island-local `x == 0` on `asteroid_miner_layout_replay_frame_cell` so Lab grid clicks on column 0 return cell detail JSON instead of HTTP 400 `invalid_x_zero`.

## Non-goals

- Do not change world-map (`WorldRawCoord`) routing rules where `x == 0` is invalid.
- Do not refactor the full coordinate-frame tagging system.
- Do not change replay serialization or canvas rendering.

## Implementation Plan

1. Trace click path: `asteroid_miner_layout_lab.js` `domIndexToWorldXY` → POST `{ x, y }` → `public_pages.py` guard → `lookup_cell_in_serialized_frame`.
2. Remove or scope the `if x == 0: return _bad("invalid_x_zero")` guard (lines 722–723) to world-map frames only, if tagging exists.
3. Confirm `lookup_cell_in_serialized_frame` already supports `x == 0` (see `test_lookup_synthetic_lab_empty_inside_island_bbox_only`).
4. Manually verify Lab cell-detail modal opens for column 0 on a frame whose bbox includes `x == 0`.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py` (`asteroid_miner_layout_replay_frame_cell`)
- `django_apps/web/services/replay_frame_cell_lookup.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `src/shapez2_factory/domain/asteroid_lab/coord_frames.py` (`IslandRawCoord`)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: N/A (integration regression deferred to Mid plan)
- build: `python manage.py check`
- manual verification: Lab replay — click cell at island-local column 0 → cell detail JSON returned, modal opens

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- World-map vs island-local frame tagging may not exist yet; guard removal may be unconditional.
- Mid plan adds integration test; Low plan adds optional view unit test.
