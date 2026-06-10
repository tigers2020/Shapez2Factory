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

# Plan: Fix Lab cell-detail for island-local column x=0 (SHA-55 High)

## Source Issue

- Linear: SHA-55
- Status at planning time: In Progress
- Priority: High

## Problem

`asteroid_miner_layout_replay_frame_cell` rejects POST bodies with `x == 0` (`invalid_x_zero`), but Lab replay frames use island-local coordinates where `x == 0` is valid. Users clicking cells on column 0 get HTTP 400 instead of cell detail JSON while the lookup service already supports `x == 0`.

## Scope

Restore correct cell-detail behavior for island-local column 0 on persisted replay frames. Mid plan covers endpoint guard removal and tests.

## Non-goals

- Changing world-map routing rules where `x == 0` is invalid.
- Refactoring coordinate-frame tagging or replay serialization.

## Implementation Plan

1. Reproduce: open Lab replay with bbox including column 0, click cell at `x == 0`, confirm HTTP 400 `invalid_x_zero` today.
2. After Mid fix, confirm modal receives cell detail JSON matching `lookup_cell_in_serialized_frame`.
3. Verify world-map endpoints (if any) still reject invalid world `x == 0` per non-goals.

## Files / Areas Likely Affected

- `django_apps/web/views/public_pages.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/web/services/replay_frame_cell_lookup.py`

## Validation Plan

- manual verification: Lab click on column 0 opens cell detail
- tests: integration regression in Mid/Low plans

## Acceptance Criteria

- [ ] POST accepts island-local `x == 0` and returns cell detail JSON.
- [ ] Lab client click path works for column 0.
- [ ] World-map invalid-x rules unchanged.

## Risks / Open Questions

- Confirm no separate world-map replay cell endpoint shares the same view without frame tagging.
