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

# Plan: Unit regression for map_view-only pattern bundle enrichment (SHA-58 Low)

## Source Issue

- Linear: SHA-58
- Status at planning time: In Progress
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`; map_view-only gap is untested.

## Scope

Add regression test for renderable frame with `map_view.full_cells` containing equipment rows and no `cell_overlay_json`, asserting `pattern_bundle_highlights` attached.

## Non-goals

- Integration/UI tests unless unit coverage insufficient.

## Implementation Plan

1. Extend `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py` with fixture frame: `fluid_miner` in `map_view.full_cells`, empty `metrics`, no `cell_overlay_json`.
2. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights` and assert non-empty `metrics.pattern_bundle_highlights` matching `build_equipment_bundles` expectation.
3. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- tests: new regression green with Mid implementation

## Acceptance Criteria

- [ ] Unit regression added for map_view-only frame.
- [ ] Existing overlay-JSON tests still pass.

## Risks / Open Questions

- Fixture must match minimal renderable frame shape the enrichment function accepts.
