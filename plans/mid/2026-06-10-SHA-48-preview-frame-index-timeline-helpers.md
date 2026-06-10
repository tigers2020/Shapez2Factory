---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Wire preview_frame_index and getTimelineFrameTotal() for lazy replay timeline

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Mid

## Problem

The server emits `preview_frame_index` in the lazy replay manifest (`lab_replay_manifest_json_dict()`), but no JS under `django_apps/web/static/` reads it. Timeline helpers use `replayFrames.length` for counter denominators while `getMaxTimelineIndex()` already uses `labReplayLoadState.frameCount` when lazy and not loaded.

## Scope

Read `preview_frame_index` from manifest during lazy init and post-solver refresh. Add `getTimelineFrameTotal()` helper and wire it into counter/scrub code paths. Store preview index on `labReplayLoadState` for reuse.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay delivery mode.
- Backend manifest schema changes.

## Implementation Plan

1. Extend `labReplayLoadState` with `previewFrameIndex: 0` (or `null` when unset).
2. In lazy init (`manifestRaw.mode === "lazy"`, ~2645–2660), set:
   - `labReplayLoadState.previewFrameIndex = Number(manifestRaw.preview_frame_index)` with `Number.isFinite` guard, fallback to `preview.frame_index` or `0`.
3. Mirror the same assignment in post-solver lazy refresh (`lazy.mode === "lazy"`, ~4520–4532).
4. Add helper near `getMaxTimelineIndex()` (~3252):

   ```javascript
   function getTimelineFrameTotal() {
     if (
       hasServerReplay &&
       labReplayLoadState.mode === "lazy" &&
       labReplayLoadState.status !== "loaded" &&
       labReplayLoadState.frameCount > replayFrames.length
     ) {
       return labReplayLoadState.frameCount;
     }
     return hasServerReplay ? replayFrames.length : TOTAL_FRAMES;
   }
   ```

5. Add helper `getLazyPreviewTimelineIndex()` returning `labReplayLoadState.previewFrameIndex` when lazy-not-loaded, else `replayArrayIndex` / `frame.frame_index`.
6. Replace `replayFrames.length` denominators in `updateFrameInfo`, `formatLabFrameCounter` call sites, and `syncLabTimelineScrub` with `getTimelineFrameTotal()`.
7. Pass `getLazyPreviewTimelineIndex()` (or equivalent) as `timelineSlotIndex` to `updateFrameInfo` during lazy preview.
8. After lazy load completes (`finalizeLazyReplayFrames`, ~2753), confirm helpers fall back to `replayFrames.length` — no behavior change post-load.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (reference only — manifest already emits field)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `pytest tests/unit/web/test_lab_lazy_replay_timeline.py -v`
- build: N/A
- manual verification: grep confirms `preview_frame_index` consumed in lab JS; lazy preview counter uses `frame_count`

## Acceptance Criteria

- [ ] `preview_frame_index` read from manifest on lazy init and post-solver refresh.
- [ ] `getTimelineFrameTotal()` returns `frameCount` when lazy and not loaded, else `replayFrames.length`.
- [ ] Counter/scrub paths use helpers instead of raw `replayFrames.length`.
- [ ] Post-load behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Manifest may omit `preview_frame_index` on older cached rows; fallback chain must be explicit (`preview.frame_index` → `0`).
- `formatLabFrameCounter` is 0-based display; confirm server `preview_frame_index` is 0-based (matches `test_lab_replay_lazy_handle.py`).
