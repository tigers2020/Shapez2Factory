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

# Plan: Read preview_frame_index and add getTimelineFrameTotal helper

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Mid

## Problem

Lazy init sets `replayFrames = [manifest.preview_frame]` (one element) while `labReplayLoadState.frameCount = manifest.frame_count`. `applyFrame()` / `updateFrameInfo()` pass `replayFrames.length` as the counter denominator (~3228, 3238, 3262). `getCurrentTimelineIndex()` returns `replayArrayIndex` (0 for preview-only array) instead of `preview_frame_index` or `frame.frame_index`. Grep shows `preview_frame_index` is present in manifest JSON from `lab_replay_manifest_json_dict()` but absent from all JS under `django_apps/web/static/`.

## Scope

Read `preview_frame_index` from manifest during lazy init and post-solver refresh. Add `getTimelineFrameTotal()` helper and wire into counter/scrub paths. Keep post-load behavior unchanged.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay delivery mode.
- Backend manifest schema changes unless JS cannot consume existing fields.

## Implementation Plan

1. During lazy init in `asteroid_miner_layout_lab.js`, parse `preview_frame_index` from `#lab-replay-manifest-data` alongside existing `frame_count` / `preview_frame` reads.
2. Store preview index in module state (e.g. `labReplayLoadState.previewFrameIndex`) and refresh after post-solver manifest update.
3. Add `getTimelineFrameTotal()`:
   - When lazy and not yet loaded: return `labReplayLoadState.frameCount`.
   - After load or inline mode: return `replayFrames.length`.
4. Replace direct `replayFrames.length` denominator usage in `updateFrameInfo`, `formatLabFrameCounter`, and `syncLabTimelineScrub` initial value with `getTimelineFrameTotal()`.
5. Update `getCurrentTimelineIndex()` to return `preview_frame_index` (or `frame.frame_index`) when lazy and preview-only array is active.
6. Confirm `getMaxTimelineIndex()` (~2845–2853) stays consistent with helper semantics.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (`lab_replay_manifest_json_dict` — reference only)
- `django_apps/web/services/asteroid_lab_page_context.py` (manifest embed — reference only)
- `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` (server contract only)

## Validation Plan

- lint: N/A (JS-only)
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py -v`
- build: `python manage.py check`
- manual verification: Lazy Lab replay with non-zero preview index; counter and scrub use manifest totals before fetch.

## Acceptance Criteria

- [ ] `preview_frame_index` read from manifest during lazy init and refresh.
- [ ] `getTimelineFrameTotal()` used in counter/scrub paths.
- [ ] Post-load behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Multiple call sites use `replayFrames.length`; incomplete wiring leaves partial mismatch.
- `preview_frame_index` contract is server-tested only; no JS regression until Low-priority test lands.
