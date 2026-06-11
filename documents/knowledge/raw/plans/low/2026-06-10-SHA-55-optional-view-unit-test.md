---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional view-level unit test for replay frame cell POST at x=0

## Source Issue

- Linear: SHA-55
- Status at planning time: In Progress
- Priority: Low

## Problem

Integration coverage for `x: 0` is the primary regression gate (Mid plan). A lightweight view unit test with a mocked serialized frame payload would catch guard regressions without full project ingest setup.

## Scope

Add an optional unit test that calls `asteroid_miner_layout_replay_frame_cell` with `x: 0` and a minimal `ReplayFrame` / mocked `serialize_replay_frame` payload.

## Non-goals

- Do not duplicate full integration ingest flow if Mid integration test is sufficient.
- Do not change production view logic (covered by High/Mid plans).

## Implementation Plan

1. Add test module or extend existing web view tests (e.g. `tests/unit/web/test_replay_frame_cell_view.py` or adjacent to lookup tests).
2. Create `ReplayFrame` + `ReplayTrack` + `Project` via factories or minimal ORM setup.
3. Patch or seed `serialize_replay_frame` to return payload with `summary.bbox` including `(0, 0)` and optional `full_map` entry.
4. POST JSON `{"replay_frame_id", "replay_track_id", "x": 0, "y": 0}` via Django test client.
5. Assert 200 and `ok: true` (not `invalid_x_zero`).
6. Run `pytest tests/unit/web/test_replay_frame_cell_view.py -v` (or chosen path).

## Files / Areas Likely Affected

- `tests/unit/web/test_replay_frame_cell_view.py` (new, TBD exact path)
- `django_apps/web/views/public_pages.py` (test target only)

## Validation Plan

- lint: `ruff check tests/unit/web/`
- tests: `pytest tests/unit/web/test_replay_frame_cell_view.py -v`
- typecheck: `mypy django_apps config src`
- build: `python manage.py check`
- manual verification: none required

## Acceptance Criteria

- [ ] View unit test documents `x: 0` acceptance with mocked/minimal frame.
- [ ] Matches the source issue spec (optional item).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional per issue spec — skip if Mid integration test provides sufficient coverage.
- Choose factory/fixture pattern consistent with nearby `tests/unit/web/` tests.
