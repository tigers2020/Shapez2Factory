---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
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

Correct lazy-preview first-paint timeline UX so counter and scrub thumb reflect manifest `frame_count` and `preview_frame_index` before full lazy load completes.

## Non-goals

- Changing lazy replay transport, compose, or cache validity (SHA-37/SHA-38).
- Inline replay delivery mode.
- Backend manifest schema changes unless required.

## Implementation Plan

1. Reproduce in browser: load a lazy replay with `frame_count > 1` and confirm counter shows `1/1` and scrub at 0 while status text shows `preview only (1/N frames)`.
2. During lazy init in `asteroid_miner_layout_lab.js`, read `preview_frame_index` from `lab-replay-manifest-data` and store on `labReplayLoadState`.
3. Initialize scrub position to `preview_frame_index` (not array slot 0) before lazy fetch completes.
4. Update `getCurrentTimelineIndex()` to return manifest preview index when only preview frame is loaded.
5. Verify post-load scrub/counter behavior unchanged after full frames arrive.

## Files / Areas Likely Affected

- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- `django_apps/asteroid_lab/services/lab_replay_lazy_handle.py` (read-only — manifest contract)
- `django_apps/web/services/asteroid_lab_page_context.py` (read-only)

## Validation Plan

- lint: N/A (JS change)
- typecheck: N/A
- tests: `powershell -File scripts/test_fast.ps1`; add JS/static contract test per Low plan
- build: N/A
- manual verification: Lazy replay with N>1 frames shows `preview_index / frame_count` and scrub at preview slot on first paint

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Lazy-preview timeline counter shows `preview_index / frame_count` before full load.
- [ ] Scrub thumb initializes at `preview_frame_index`, not array slot 0.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Mid-plan helper wiring (`getTimelineFrameTotal`) must stay consistent with this fix; coordinate with `plans/mid/2026-06-10-SHA-48-lazy-timeline-manifest-wiring.md`.
