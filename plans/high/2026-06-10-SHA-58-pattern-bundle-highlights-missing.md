---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Restore equipment-group coloring on map_view-only timeline frames

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only derives highlights from `cell_overlay_json.equipment_bundles`. Frames with equipment in `map_view.full_cells` but no overlay JSON ship without `metrics.pattern_bundle_highlights`, so Lab client equipment-group coloring/outline is missing.

## Scope

Align enrichment with adapter fallback: derive equipment bundles from renderable `map_view` cell rows when overlay JSON is absent, emit `metrics.pattern_bundle_highlights`.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights.
- Refactoring entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics.

## Implementation Plan

1. Reproduce: renderable frame with `map_view.full_cells` containing `fluid_miner`, empty `metrics` → no highlights.
2. Read `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame` fallback path.
3. In `enrich_lab_timeline_frames_with_pattern_bundle_highlights`, when overlay lacks `equipment_bundles`, collect rows from `map_view.full_cells` with adapter row shape.
4. Call `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire`.
5. Attach resulting wire to `frame.metrics.pattern_bundle_highlights`.
6. Verify Lab JS reads highlights on affected frames.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (reference)
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (consumer)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- manual verification: frame without overlay JSON shows equipment bundle coloring in Lab.

## Acceptance Criteria

- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.
- [ ] Enrichment path matches adapter fallback semantics.
- [ ] Existing overlay-JSON path unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Row shape normalization (`cell_kind` vs `kind`) must mirror adapter exactly.
