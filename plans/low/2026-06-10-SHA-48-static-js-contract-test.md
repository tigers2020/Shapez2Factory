---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Static JS contract test for lazy replay manifest field consumption

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` covers server manifest contract only. No JS regression guards that client code reads `preview_frame_index` or uses manifest `frame_count` for timeline denominator before lazy load. A future edit could reintroduce the `1 / 1` counter mismatch without test failure.

## Scope

Add a static JS contract test (similar to `tests/unit/web/test_lab_island_raw_coord_frame.py`) asserting manifest fields `preview_frame_index` and `frame_count` are consumed by `asteroid_miner_layout_lab.js` timeline paths.

## Non-goals

- Browser/Playwright end-to-end Lab timeline test.
- Changing lazy replay transport or backend manifest schema.
- Full JS unit test framework for Lab replay module.

## Implementation Plan

1. Review `tests/unit/web/test_lab_island_raw_coord_frame.py` pattern for static source contract assertions.
2. Add test module (e.g. extend `tests/unit/web/test_lab_island_raw_coord_frame.py` or new `tests/unit/web/test_lab_lazy_replay_timeline_contract.py`).
3. Assert `asteroid_miner_layout_lab.js` references `preview_frame_index` (or equivalent manifest read).
4. Assert `getTimelineFrameTotal` (or equivalent) uses `frameCount` / manifest total when lazy-not-loaded.
5. Assert counter/scrub paths do not use bare `replayFrames.length` as sole lazy-preview denominator (grep-based or AST-lite check per existing pattern).
6. Run: `pytest tests/unit/web/test_lab_island_raw_coord_frame.py -v` plus new test file.

## Files / Areas Likely Affected

- New or extended test under `tests/unit/web/` (e.g. `test_lab_lazy_replay_timeline_contract.py`)
- `tests/unit/web/test_lab_island_raw_coord_frame.py` (pattern reference)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (subject under test; changed in Mid scope)
- `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` (server contract reference)

## Validation Plan

- lint: `ruff check tests/unit/web/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_lab_island_raw_coord_frame.py tests/unit/web/test_lab_lazy_replay_timeline_contract.py -v` (adjust path to actual new file)
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Static contract test fails if `preview_frame_index` consumption is removed.
- [ ] Test documents expected manifest field wiring for lazy timeline.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Static grep tests can be brittle if refactor renames symbols without changing behavior — prefer assertions on stable manifest field names.
- Depends on Mid scope landing helper/read logic before test is meaningful.
