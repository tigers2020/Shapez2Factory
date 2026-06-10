---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Wire manifest frame_count and preview_frame_index into lazy timeline helpers

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Mid

## Problem

`getMaxTimelineIndex()` uses `labReplayLoadState.frameCount` but `updateFrameInfo()` / `formatLabFrameCounter()` use `replayFrames.length`, causing denominator mismatch during lazy preview.

## Scope

Add `getTimelineFrameTotal()` helper and wire manifest fields into counter/scrub paths in `asteroid_miner_layout_lab.js`.

## Non-goals

- Backend manifest schema changes.
- Inline replay mode changes.

## Implementation Plan

1. Read `preview_frame_index` from manifest JSON during lazy init and post-solver refresh paths.
2. Add `getTimelineFrameTotal()` returning `labReplayLoadState.frameCount` when lazy and not yet loaded, else `replayFrames.length`.
3. Replace direct `replayFrames.length` usage in `updateFrameInfo`, `formatLabFrameCounter`, and `syncLabTimelineScrub` initial value with the helper.
4. Ensure `applyFrame()` uses manifest-aware index for counter display during preview-only state.
5. Grep `asteroid_miner_layout_lab.js` for other `replayFrames.length` timeline usages and align.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/web/static/web/js/lab_replay_canvas_renderer.js` (read-only check)
- `django_apps/web/static/web/js/lab_replay_canvas_terrain.js` (read-only check)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `tests/unit/web/test_lab_island_raw_coord_frame.py` (pattern reference); extend per Low plan
- build: N/A
- manual verification: Counter denominator matches `frame_count` before lazy load; unchanged after load

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] `preview_frame_index` consumed from manifest during lazy init.
- [ ] Post-load behavior unchanged.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- High-plan scrub initialization depends on this helper; implement together in one PR.
