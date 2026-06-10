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

# Plan: Fix lazy-preview timeline counter/scrub mismatch on first paint

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: High

## Problem

In lazy replay delivery mode, the Lab timeline chrome uses inconsistent frame totals before the lazy JSON fetch completes. The scrubber maximum is derived from `manifest.frame_count`, but the frame counter and scrub position use the in-memory preview array length (`replayFrames.length === 1`). Operators see counter `1 / 1` and scrub at slot 0 even when the status line correctly says `preview only (1/100 frames)`.

## Scope

Fix first-paint timeline counter and scrub thumb so they reflect manifest `frame_count` and `preview_frame_index` before lazy load completes. Wire `getCurrentTimelineIndex()` and counter denominator paths to use manifest-aware totals instead of `replayFrames.length` alone.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay delivery mode.
- Backend manifest schema changes unless required for the JS fix.

## Implementation Plan

1. Read `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` lazy init block (~2636–2660) and timeline helpers (~3252–3302).
2. Add `getTimelineFrameTotal()` returning `labReplayLoadState.frameCount` when lazy and not loaded, else `replayFrames.length`.
3. Update `getCurrentTimelineIndex()` to return `labReplayLoadState.previewFrameIndex` (stored from manifest) when lazy and not loaded, instead of `replayArrayIndex` (always 0 for single-element preview array).
4. Replace `replayFrames.length` denominator in `updateFrameInfo()` call sites (~3666, 3677, 3701) with `getTimelineFrameTotal()`.
5. Ensure `syncLabTimelineScrub()` uses `getCurrentTimelineIndex()` so scrub thumb initializes at preview slot, not 0.
6. Manual verify: open Lab with lazy replay (100+ frames), confirm counter shows `preview_index / frame_count` and scrub near preview slot before fetch completes.
7. Confirm post-load behavior unchanged after lazy fetch resolves.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (manifest data element, if init reads from DOM)

## Validation Plan

- lint: N/A (JS; no ruff scope)
- typecheck: N/A
- tests: `pytest tests/unit/web/test_lab_island_raw_coord_frame.py -v` (baseline); add SHA-48 contract test in Low plan
- build: N/A
- manual verification: Lab lazy replay page — counter/scrub match status line before and after load

## Acceptance Criteria

- [ ] Lazy-preview timeline counter shows `preview_index / frame_count` before full load.
- [ ] Scrub thumb initializes at `preview_frame_index`, not array slot 0.
- [ ] Post-load behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Mid/Low tasks must land helper and contract test; this High slice depends on `preview_frame_index` being stored during lazy init (Mid plan).
