---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for map_view-only pattern-bundle enrichment

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`; map_view-only frames are untested.

## Scope

Add unit regression asserting a renderable frame with `map_view.full_cells` (no `cell_overlay_json`) receives `pattern_bundle_highlights`.

## Non-goals

- Changing enrichment implementation (covered in Mid/High plans).
- Integration/browser tests.

## Implementation Plan

1. Add fixture frame: renderable, `map_view.full_cells` with one `fluid_miner`, empty `metrics`, no `cell_overlay_json`.
2. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])`.
3. Assert `frame["metrics"]["pattern_bundle_highlights"]` is non-empty and matches `build_equipment_bundles` expectation.
4. Add negative control: frame without miners still has no highlights.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- typecheck: n/a
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test should land with or immediately after Mid implementation to avoid red CI.
