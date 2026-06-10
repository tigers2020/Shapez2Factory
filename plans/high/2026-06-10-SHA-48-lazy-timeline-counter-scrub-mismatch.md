---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fix lazy-preview timeline counter and scrub mismatch on first paint

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: High

## Problem

In lazy replay delivery mode, before the lazy JSON fetch completes, the Lab timeline chrome shows inconsistent frame totals. The scrubber max already uses `manifest.frame_count` via `getMaxTimelineIndex()`, but the frame counter denominator and scrub thumb position use the in-memory preview array (`replayFrames.length === 1`) and `replayArrayIndex` (array slot 0). Operators see `1 / 1` with scrub at slot 0 while the status line correctly says `preview only (1/100 frames)`.

## Scope

Align lazy-preview timeline counter display and scrub thumb initial position with manifest `frame_count` and `preview_frame_index` on first paint. Depends on Mid plan helpers (`getTimelineFrameTotal()`, `preview_frame_index` wiring) but this High slice owns the user-visible mismatch fix end-to-end.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay delivery mode behavior.
- Backend manifest schema changes.

## Implementation Plan

1. After Mid helpers land, verify lazy init (`manifestRaw.mode === "lazy"`) sets `replayArrayIndex` to `preview_frame_index` (not array slot 0) when only a preview frame is loaded.
2. Replace all lazy-preview counter denominators that pass `replayFrames.length` with `getTimelineFrameTotal()` in `applyFrame()` chrome paths (~3666, 3677, 3701).
3. Update `getCurrentTimelineIndex()` to return manifest `preview_frame_index` (or `frame.frame_index`) during lazy-not-loaded preview, not `replayArrayIndex` when they diverge.
4. Ensure `syncLabTimelineScrub()` sets `scrubEl.value` to the manifest timeline index on bootstrap, not array index 0.
5. Confirm `renderLabReplayLoadStatus()` preview text, frame counter, and scrub thumb all agree (e.g. `48 / 100` with thumb near slot 48).
6. Manual verify: load Lab page with lazy replay (100+ frames), before fetch completes check counter, scrub, and status line.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (`applyFrame`, `getCurrentTimelineIndex`, `syncLabTimelineScrub`, lazy init, post-solver refresh ~4520–4547)

## Validation Plan

- lint: N/A (JS in static bundle)
- typecheck: N/A
- tests: `pytest tests/unit/web/test_lab_lazy_replay_timeline.py -v` (after Low plan adds contract test)
- build: N/A
- manual verification: Lab lazy replay page — counter shows `preview_index / frame_count`, scrub at `preview_frame_index` before full load; after load, inline behavior unchanged

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

- Scrub drag before lazy load completes may request frames not yet in `replayFrames`; confirm `setTimelineIndex` clamps to loaded preview only or triggers lazy fetch as today.
- `replaySlotForServerInitialFrame()` currently searches array slots; lazy preview may need a separate initial-index path when `replayFrames.length === 1`.
