---
linear_issue: SHA-55
title: Replay frame cell POST rejects island-local x=0 (invalid_x_zero)
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Optional view unit test for x=0 POST with mocked frame

## Source Issue

- Linear: SHA-55
- Status at planning time: Todo
- Priority: Low

## Problem

Integration coverage for `x == 0` is the primary regression gate; an optional fast unit test on the view can catch guard regressions without DB setup.

## Scope

Add an optional unit test on `asteroid_miner_layout_replay_frame_cell` using a minimal mocked frame payload that asserts `x: 0` is accepted.

## Non-goals

- Do not duplicate full integration coverage from the Mid plan.
- Do not change view behavior (implementation belongs in High/Mid plans).

## Implementation Plan

1. Add unit test under `tests/unit/web/` (new or existing module) mocking the frame lookup path with a minimal serialized payload containing `(0, y)`.
2. POST or call the view with `x=0`; assert non-400 response and expected lookup delegation.
3. Run `pytest tests/unit/web/ -v -k invalid_x_zero` (or chosen test name).

## Files / Areas Likely Affected

- `tests/unit/web/` (new or extended test module)
- `django_apps/web/views/public_pages.py` (test target only)

## Validation Plan

- lint: `ruff check tests/unit/web/`
- typecheck: n/a
- tests: `pytest tests/unit/web/ -v -k x_zero`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Optional unit test added or explicitly skipped with reason documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- View unit tests may require heavier mocking than integration tests; skip if mock surface is brittle.
