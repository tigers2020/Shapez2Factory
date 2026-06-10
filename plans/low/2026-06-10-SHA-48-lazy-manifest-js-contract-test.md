---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Static JS contract test for lazy manifest field consumption

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Low

## Problem

Server-side lazy replay manifest contract is tested (`test_lab_replay_lazy_handle.py`), but no regression guards that client JS actually consumes `preview_frame_index` and uses `frame_count` for timeline totals. A future refactor could reintroduce the 1/N mismatch without test failure.

## Scope

Add a static JS contract test (pattern from `test_lab_island_raw_coord_frame.py`) asserting that `asteroid_miner_layout_lab.js` references `preview_frame_index`, `getTimelineFrameTotal`, and uses manifest `frame_count` for lazy timeline denominator.

## Non-goals

- Browser/Playwright E2E for this slice (optional follow-up).
- Backend manifest tests (already covered).

## Implementation Plan

1. Create `tests/unit/web/test_lab_lazy_timeline_manifest_contract.py`.
2. Follow `test_lab_island_raw_coord_frame.py` pattern: read `LAB_JS` path, assert substring presence.
3. Assert required symbols/strings exist after Mid/High implementation:
   - `preview_frame_index` (manifest read)
   - `getTimelineFrameTotal` (helper name)
   - `previewFrameIndex` (state field)
4. Optionally assert `updateFrameInfo` call sites no longer pass bare `replayFrames.length` as sole lazy denominator (grep-based negative check or positive check for `getTimelineFrameTotal()`).
5. Run: `pytest tests/unit/web/test_lab_lazy_timeline_manifest_contract.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_lab_lazy_timeline_manifest_contract.py` (create)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (read-only reference)

## Validation Plan

- lint: `ruff check tests/unit/web/test_lab_lazy_timeline_manifest_contract.py`
- typecheck: `mypy tests/unit/web/test_lab_lazy_timeline_manifest_contract.py` (if in scope)
- tests: `pytest tests/unit/web/test_lab_lazy_timeline_manifest_contract.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test added asserting manifest field consumption in JS.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Static substring tests are brittle to renames; keep assertions on stable public manifest field names from server contract.
