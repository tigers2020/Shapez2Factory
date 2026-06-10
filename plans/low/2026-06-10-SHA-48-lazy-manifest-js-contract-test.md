---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Add static JS contract test for lazy replay manifest field consumption

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Low

## Problem

Server contract for lazy replay manifest includes `preview_frame_index`, and `getMaxTimelineIndex()` already branches on lazy load state, but there is no JS regression test asserting the client consumes manifest timeline fields. `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` covers server only.

## Scope

Add a static contract test (pattern from `test_lab_island_raw_coord_frame.py`) asserting `asteroid_miner_layout_lab.js` reads `preview_frame_index`, defines `getTimelineFrameTotal()`, and uses it in timeline counter/scrub paths.

## Non-goals

- Playwright/browser E2E for this slice.
- Backend manifest schema changes.
- Changing lazy replay transport or compose.

## Implementation Plan

1. Create `tests/unit/web/test_lab_lazy_replay_timeline.py` modeled on `test_lab_island_raw_coord_frame.py`.
2. Read `asteroid_miner_layout_lab.js` as text; assert presence of:
   - `preview_frame_index` (manifest read)
   - `function getTimelineFrameTotal` (or equivalent named helper)
   - `labReplayLoadState.previewFrameIndex` (or chosen state field name)
   - `getTimelineFrameTotal()` referenced in `updateFrameInfo` / `applyFrame` / `syncLabTimelineScrub` neighborhood
3. Assert `getMaxTimelineIndex` still references `labReplayLoadState.frameCount` for lazy-not-loaded branch (existing behavior preserved).
4. Optional: assert `preview_frame_index` absent from grep before fix would fail — document as regression guard only after Mid implementation lands.
5. Run `pytest tests/unit/web/test_lab_lazy_replay_timeline.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_lab_lazy_replay_timeline.py` (new)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (implementation target for Mid/High plans)

## Validation Plan

- lint: `ruff check tests/unit/web/test_lab_lazy_replay_timeline.py`
- typecheck: covered by `mypy` scope if typed
- tests: `pytest tests/unit/web/test_lab_lazy_replay_timeline.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test added asserting manifest `preview_frame_index` consumption in lab JS.
- [ ] Test fails on pre-fix JS (verify once when implementing).
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Static string assertions are brittle to renames; keep assertions focused on contract symbols, not line numbers.
- Full behavioral coverage still needs manual or Playwright verification (High plan).
