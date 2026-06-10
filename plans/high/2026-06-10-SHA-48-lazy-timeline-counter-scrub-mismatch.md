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
- Status at planning time: In Progress
- Priority: High

## Problem

In lazy replay delivery mode, the Lab timeline chrome uses inconsistent frame totals before the lazy JSON fetch completes. The scrubber maximum is derived from `manifest.frame_count`, but the frame counter and scrub position use the in-memory preview array length (`replayFrames.length === 1`). The manifest field `preview_frame_index` is emitted by the server but never read by the client, so a preview of the last equipment frame shows scrub at slot 0 and counter `1 / 1` even when the status line correctly says `preview only (1/100 frames)`.

## Scope

Align lazy-preview timeline counter and scrub thumb on first paint so they reflect manifest `frame_count` and `preview_frame_index`, consistent with `renderLabReplayLoadStatus()` preview text. Primary file: `asteroid_miner_layout_lab.js`.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay delivery mode.
- Backend manifest schema changes unless required for the JS fix.

## Implementation Plan

1. Reproduce lazy-preview state: `replayFrames = [preview]`, `labReplayLoadState.frameCount = N`, `labReplayLoadState.status !== "loaded"`.
2. Add `getTimelineFrameTotal()` returning `labReplayLoadState.frameCount` when lazy and not loaded, else `replayFrames.length`.
3. Update `getCurrentTimelineIndex()` to return `labReplayLoadState.previewFrameIndex` (or `frame.frame_index`) during lazy preview instead of `replayArrayIndex` (0).
4. Replace `replayFrames.length` denominator in `applyFrame()` / `updateFrameInfo()` call sites (~3666, 3677, 3701) with `getTimelineFrameTotal()`.
5. Initialize `replayArrayIndex` to `preview_frame_index` during lazy init and post-solver refresh (~2645–2657, ~4524–4531).
6. Verify scrub max already uses `getMaxTimelineIndex()` (correct); confirm counter and scrub thumb match after fix.
7. Manual check: lazy replay with 100 frames shows e.g. `48 / 100` and scrub near preview slot before full load.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (reference only; manifest contract)
- `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` (server contract reference)

## Validation Plan

- lint: N/A (JS; no ruff scope)
- typecheck: N/A
- tests: `pytest tests/unit/web/test_lab_lazy_replay_timeline_manifest.py -v` (see Low plan)
- build: N/A
- manual verification: Load Lab page with lazy replay manifest; confirm counter `preview_index+1 / frame_count` and scrub at `preview_frame_index` before fetch completes; after load, counter uses `replayFrames.length`.

## Acceptance Criteria

- [ ] Lazy-preview timeline counter shows `preview_index / frame_count` before full load.
- [ ] Scrub thumb initializes at `preview_frame_index`, not array slot 0.
- [ ] Post-load behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Scrubbing to unloaded frame indices before lazy fetch completes may need guard in `setTimelineIndex` (defer or trigger load); verify existing lazy-load-on-scrub behavior.
- Post-solver refresh path (~4524) must mirror initial manifest init for `preview_frame_index`.
