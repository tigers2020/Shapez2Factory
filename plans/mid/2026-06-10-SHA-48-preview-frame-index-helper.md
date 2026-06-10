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

# Plan: Read preview_frame_index and add getTimelineFrameTotal helper

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Mid

## Problem

The server emits `preview_frame_index` in the lazy replay manifest (`lab_replay_manifest_json_dict()` in `lab_replay_lazy_handle.py`), but no JS under `django_apps/web/static/` reads it. Lazy init stores `frame_count` and `preview_frame` object but not the index, so timeline helpers cannot position scrub or counter correctly.

## Scope

Read `preview_frame_index` from manifest during lazy init and post-solver refresh. Add `getTimelineFrameTotal()` helper and wire it into counter/scrub code paths that currently use `replayFrames.length`.

## Non-goals

- Backend manifest schema changes.
- Inline replay mode changes.
- Lazy fetch transport or cache validity (SHA-37/SHA-38).

## Implementation Plan

1. Extend `labReplayLoadState` object (~2636) with `previewFrameIndex: 0`.
2. During lazy init from `manifestRaw` (~2646–2658), set:
   - `labReplayLoadState.previewFrameIndex = Number(manifestRaw.preview_frame_index) || 0`
   - `replayArrayIndex = labReplayLoadState.previewFrameIndex` (when lazy and not loaded)
3. Mirror the same in post-solver refresh path (~4524–4535) when `lazy.preview_frame_index` is present.
4. Implement `getTimelineFrameTotal()`:
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
5. Update `formatLabFrameCounter` call sites and `updateFrameInfo` to pass `getTimelineFrameTotal()` as denominator.
6. Update `getCurrentTimelineIndex()` to return `labReplayLoadState.previewFrameIndex` when lazy preview-only, else existing logic.
7. Run existing unit tests: `pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (reference only; manifest contract)
- `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` (server contract baseline)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py tests/unit/web/test_lab_island_raw_coord_frame.py -v`
- build: N/A
- manual verification: lazy init reads manifest; counter denominator uses frameCount

## Acceptance Criteria

- [ ] `preview_frame_index` read from manifest during lazy init and post-solver refresh.
- [ ] `getTimelineFrameTotal()` wired into counter/scrub paths.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Must coordinate with High plan slice to avoid conflicting edits in same functions.
- `replayArrayIndex` used for frame lookup — ensure preview frame array index stays 0 while display index uses `preview_frame_index`.
