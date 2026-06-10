---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire preview_frame_index and getTimelineFrameTotal helper

## Source Issue

- Linear: SHA-48
- Status at planning time: In Progress
- Priority: Mid

## Problem

Lazy init reads `manifestRaw.preview_frame` but ignores `manifestRaw.preview_frame_index`. Counter/scrub paths pass `replayFrames.length` as denominator and `replayArrayIndex` as slot, causing `1 / 1` and scrub at 0 while manifest reports N frames.

## Scope

Read `preview_frame_index` from manifest during lazy init and post-solver refresh; add `getTimelineFrameTotal()` helper; wire into counter/scrub paths. Depends on High plan for end-to-end UX fix.

## Non-goals

- Backend manifest schema changes.
- Inline replay mode changes.
- Lazy transport/compose changes.

## Implementation Plan

1. Extend `labReplayLoadState` with `previewFrameIndex: 0` field.
2. During lazy init (`manifestRaw.mode === "lazy"`), set `labReplayLoadState.previewFrameIndex = Number(manifestRaw.preview_frame_index) || 0`.
3. Mirror same assignment in post-solver refresh block (~4524–4531) from `lazy.preview_frame_index`.
4. Add helper after `getMaxTimelineIndex()`:

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

5. Update `getCurrentTimelineIndex()`:

```javascript
function getCurrentTimelineIndex() {
  if (!hasServerReplay) return frame;
  if (
    labReplayLoadState.mode === "lazy" &&
    labReplayLoadState.status !== "loaded" &&
    labReplayLoadState.frameCount > replayFrames.length
  ) {
    return labReplayLoadState.previewFrameIndex;
  }
  return replayArrayIndex;
}
```

6. Set `replayArrayIndex = labReplayLoadState.previewFrameIndex` after lazy init when preview frame is present.
7. Replace `replayFrames.length` with `getTimelineFrameTotal()` in `updateFrameInfo`, `formatLabFrameCounter` call sites inside `applyFrame`, and any toolbar cycle display using array length as total.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (`lab_replay_manifest_json_dict` — reference)

## Validation Plan

- tests: `pytest tests/unit/web/test_lab_lazy_replay_timeline_manifest.py -v`
- manual verification: Grep JS confirms `preview_frame_index` consumed; lazy preview counter uses manifest total.

## Acceptance Criteria

- [ ] `preview_frame_index` read from manifest on lazy init and post-solver refresh.
- [ ] `getTimelineFrameTotal()` used for counter denominator before lazy load completes.
- [ ] Post-load paths use `replayFrames.length` unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- `preview_frame.frame_index` may differ from manifest `preview_frame_index`; prefer manifest field as authority per server contract in `lab_replay_lazy_handle.py`.
