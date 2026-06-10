---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: High
labels:
  - bug
  - ui
  - test
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Fix lazy-preview timeline counter/scrub mismatch on first paint

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: High

## Problem

In lazy replay delivery mode, the Lab timeline chrome uses inconsistent frame totals before the lazy JSON fetch completes. The scrubber maximum is derived from `manifest.frame_count`, but the frame counter and scrub position use the in-memory preview array length (`replayFrames.length === 1`). The manifest field `preview_frame_index` is emitted by the server but never read by the client, so a preview of the last equipment frame shows scrub at slot 0 and counter `1 / 1` even when the status line correctly says `preview only (1/100 frames)`.

## Scope

Align lazy-preview timeline UI on first paint so counter and scrub thumb reflect manifest `frame_count` and `preview_frame_index`, consistent with `renderLabReplayLoadStatus()` preview text. Post-load behavior must remain unchanged.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (see SHA-37/SHA-38).
- Inline replay delivery mode.
- Backend manifest schema changes unless required for the JS fix.

## Implementation Plan

1. Reproduce in Lab lazy mode: long replay with preview of a non-zero frame index; confirm counter shows `1 / 1` and scrub at 0 while status line shows `preview only (1/N frames)`.
2. Read `preview_frame_index` from `#lab-replay-manifest-data` during lazy init and post-solver refresh in `asteroid_miner_layout_lab.js`.
3. Add `getTimelineFrameTotal()` returning `labReplayLoadState.frameCount` when lazy and not loaded, else `replayFrames.length`.
4. Wire helper into `updateFrameInfo`, `formatLabFrameCounter`, `syncLabTimelineScrub`, and `getCurrentTimelineIndex()` so counter shows `preview_index / frame_count` and scrub initializes at `preview_frame_index`.
5. Manual verify: counter `48 / 100` with scrub near preview slot before full load; post-load scrub/counter unchanged.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (`getMaxTimelineIndex`, `applyFrame`, `updateFrameInfo`, `getCurrentTimelineIndex`, lazy init)
- `django_apps/web/static/web/js/lab_replay_canvas_renderer.js` (reference only)
- `django_apps/web/static/web/js/lab_replay_canvas_terrain.js` (reference only)
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (`lab_replay_manifest_json_dict`, `preview_frame_index` contract)
- `django_apps/web/services/asteroid_lab_page_context.py` (manifest embed reference)

## Validation Plan

- lint: N/A (JS-only change; run project JS lint if configured)
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v` (server contract unchanged)
- build: `python manage.py check`
- manual verification: Load Lab page in lazy replay mode with 100+ frames; confirm first-paint counter/scrub match manifest before lazy JSON fetch completes.

## Acceptance Criteria

- [ ] Lazy-preview timeline counter shows `preview_index / frame_count` before full load.
- [ ] Scrub thumb initializes at `preview_frame_index`, not array slot 0.
- [ ] Post-load behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `getMaxTimelineIndex()` already uses `frameCount - 1` when lazy; counter/scrub paths diverge because they still pass `replayFrames.length` — fix must touch all call sites, not scrub max alone.
- Post-solver manifest refresh must re-read `preview_frame_index` or timeline may regress after async solver completion.
- Coordinate with SHA-37/SHA-38 backend cache fixes; timeline fix is independent but same Lab page surface.
