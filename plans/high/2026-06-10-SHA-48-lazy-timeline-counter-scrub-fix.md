---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fix lazy-preview timeline counter and scrub mismatch

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: High

## Problem

In lazy replay mode, scrubber max uses `manifest.frame_count` but counter and scrub position use `replayFrames.length` (1). `preview_frame_index` from server is never read, so operators see `1/1` and scrub at 0 while status text says `preview only (1/100 frames)`.

## Scope

Align lazy-preview timeline UI in `asteroid_miner_layout_lab.js` before full lazy load completes.

## Non-goals

- Lazy transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay mode.
- Backend manifest schema changes unless required.

## Implementation Plan

1. Read `preview_frame_index` from `lab-replay-manifest-data` during lazy init and post-solver refresh.
2. Add `getTimelineFrameTotal()` — return `labReplayLoadState.frameCount` when lazy and not loaded, else `replayFrames.length`.
3. Wire helper into `updateFrameInfo`, `formatLabFrameCounter`, `syncLabTimelineScrub` initial value.
4. Set `getCurrentTimelineIndex()` to use `preview_frame_index` / `frame.frame_index` during lazy preview, not array slot 0.
5. Manual verify: lazy preview of 100-frame replay shows `48/100` (example) with scrub at preview index.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (reference)
- `django_apps/web/services/asteroid_lab_page_context.py` (reference)

## Validation Plan

- tests: mid/low plans add automated coverage
- manual verification: lazy preview counter/scrub match manifest

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Post-load behavior must remain unchanged — test both paths.
