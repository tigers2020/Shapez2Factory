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
- Priority: Low

## Problem

No JS regression asserts that `preview_frame_index` and `frame_count` are consumed by timeline chrome.

## Scope

Add static contract test similar to `test_lab_island_raw_coord_frame.py`.

## Implementation Plan

1. Review `tests/unit/web/test_lab_island_raw_coord_frame.py` pattern.
2. Add `tests/unit/web/test_lab_lazy_timeline_manifest_contract.py` grepping `asteroid_miner_layout_lab.js` for `preview_frame_index`, `getTimelineFrameTotal`, `frameCount`.
3. Run `pytest tests/unit/web/test_lab_lazy_timeline_manifest_contract.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_lab_lazy_timeline_manifest_contract.py` (new)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

## Validation Plan

- tests: new contract test

## Acceptance Criteria

- [ ] Test fails if manifest fields are removed from JS.

## Risks / Open Questions

- Static grep test is weak but matches repo pattern for JS contracts.
