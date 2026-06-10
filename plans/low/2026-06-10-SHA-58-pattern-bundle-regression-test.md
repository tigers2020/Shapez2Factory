---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for map_view-only pattern bundle highlights

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`. No test for map_view-only frames.

## Scope

Add unit regression test for renderable frame with `map_view.full_cells` but no `cell_overlay_json`, asserting highlights are attached.

## Non-goals

- Full Lab client render test.
- Testing every equipment bundle permutation.

## Implementation Plan

1. Read existing tests in `test_lab_timeline_pattern_bundle_enrichment.py`.
2. Add fixture: renderable frame with `fluid_miner` in `map_view.full_cells`, empty `metrics`, no `cell_overlay_json`.
3. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights`.
4. Assert `pattern_bundle_highlights` present in output frame metrics.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing first; test will fail until fallback is implemented.
