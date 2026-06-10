---
linear_issue: SHA-48
title: Lab lazy replay timeline shows 1/N counter and scrub at 0 while manifest reports N frames
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Add static JS contract test for lazy manifest field consumption

## Source Issue

- Linear: SHA-48
- Status at planning time: Todo
- Priority: Low

## Problem

Server contract is covered by `tests/unit/asteroid_lab/test_lab_replay_lazy_handle.py` but no JS regression asserts that `preview_frame_index` and `frame_count` are consumed by timeline code.

## Scope

Add a static JS contract test (similar to `test_lab_island_raw_coord_frame.py`) asserting manifest fields are read and used in timeline helpers.

## Non-goals

- Full browser E2E for lazy replay (unless existing Playwright harness already covers Lab).
- Changing server manifest emission.

## Implementation Plan

1. Review `tests/unit/web/test_lab_island_raw_coord_frame.py` for static JS assertion pattern.
2. Add test file (e.g. `tests/unit/web/test_lab_lazy_timeline_manifest_contract.py`) that reads `asteroid_miner_layout_lab.js` and asserts references to `preview_frame_index` and `getTimelineFrameTotal` (or equivalent).
3. Optionally add minimal fixture manifest JSON and unit-test helper logic if extractable without browser.
4. Run `powershell -File scripts/test_fast.ps1` to confirm test passes.

## Files / Areas Likely Affected

- `tests/unit/web/test_lab_lazy_timeline_manifest_contract.py` (new)
- `tests/unit/web/test_lab_island_raw_coord_frame.py` (pattern reference)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (read by test)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/web/test_lab_lazy_timeline_manifest_contract.py -v`
- build: N/A
- manual verification: Test fails if manifest field consumption is removed from JS

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Regression test added or updated.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Static string-matching tests are brittle; prefer testing extracted pure helpers if refactor is small enough.
