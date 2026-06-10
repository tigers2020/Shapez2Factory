---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Static JS contract test for lazy manifest field consumption

## Source Issue

- Linear: SHA-48
- Status at planning time: In Progress
- Priority: Low

## Problem

`preview_frame_index` is present in manifest JSON from `lab_replay_manifest_json_dict()` but absent from all JS under `django_apps/web/static/`. No regression test guards client consumption of lazy manifest fields.

## Scope

Add a static JS contract test (pattern: `tests/unit/web/test_lab_island_raw_coord_frame.py`) asserting `asteroid_miner_layout_lab.js` reads and uses `preview_frame_index` and `getTimelineFrameTotal` (or equivalent manifest-aware total).

## Non-goals

- Browser/Playwright E2E for timeline scrub.
- Backend manifest schema changes.
- Changing lazy transport.

## Implementation Plan

1. Create `tests/unit/web/test_lab_lazy_replay_timeline_manifest.py`.
2. Read `LAB_JS = REPO / "django_apps/web/static/web/js/asteroid_miner_layout_lab.js"`.
3. Assert source contains:
   - `preview_frame_index` (manifest read during lazy init)
   - `getTimelineFrameTotal` function definition
   - `previewFrameIndex` on `labReplayLoadState` or equivalent state field
   - `getTimelineFrameTotal()` used in counter path (not bare `replayFrames.length` alone for lazy preview)
4. Optionally assert `getCurrentTimelineIndex` references `previewFrameIndex` during lazy-not-loaded branch.
5. Run `pytest tests/unit/web/test_lab_lazy_replay_timeline_manifest.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_lab_lazy_replay_timeline_manifest.py` (new)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (implementation from High/Mid plans)

## Validation Plan

- tests: `pytest tests/unit/web/test_lab_lazy_replay_timeline_manifest.py -v`
- lint: `ruff check tests/unit/web/test_lab_lazy_replay_timeline_manifest.py`

## Acceptance Criteria

- [ ] Static test fails before JS fix, passes after.
- [ ] Asserts manifest `preview_frame_index` consumption.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Static string assertions are brittle to refactors; keep assertions on public contract symbols (`preview_frame_index`, helper name) not line numbers.
