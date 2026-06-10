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
- Priority: Mid

## Problem

Manifest emits `preview_frame_index` and `frame_count` but JS ignores them for counter/scrub during lazy preview.

## Scope

Implement helper and manifest field consumption in `asteroid_miner_layout_lab.js`.

## Implementation Plan

1. Parse `preview_frame_index` from manifest JSON on lazy init (~lines near `replayFrames = [manifest.preview_frame]`).
2. Implement `getTimelineFrameTotal()` per high plan.
3. Replace `replayFrames.length` denominator in `applyFrame` / `updateFrameInfo` (~3228, 3238, 3262).
4. Initialize scrub from `preview_frame_index` in `syncLabTimelineScrub`.
5. Run existing web unit tests: `pytest tests/unit/web/test_lab_island_raw_coord_frame.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

## Validation Plan

- tests: `pytest tests/unit/web/ -k lab -v` (existing)
- manual: lazy preview UI check

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Post-load behavior unchanged.

## Risks / Open Questions

- Coordinate with high plan — may be same PR.
