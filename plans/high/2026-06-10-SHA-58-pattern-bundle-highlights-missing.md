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

# Plan: Restore pattern-bundle highlights on map_view-only frames

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only reads `cell_overlay_json.equipment_bundles`. Renderable frames with miners in `map_view.full_cells` but no overlay JSON ship without `metrics.pattern_bundle_highlights`, so Lab client equipment-group coloring/outline is missing.

## Scope

When overlay JSON is absent or lacks `equipment_bundles`, derive bundles from `map_view.full_cells` (and overlay cells) using the same helper path as `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame`, then emit highlights.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights
- Full timeline adapter refactor
- UI changes beyond correct metrics on affected frames

## Implementation Plan

1. Reproduce: build a renderable frame with `map_view.full_cells` containing a `fluid_miner` row, empty `metrics`, no `cell_overlay_json`; call `enrich_lab_timeline_frames_with_pattern_bundle_highlights` — confirm no highlights today while `build_equipment_bundles(rows)` returns a bundle.
2. Read `lab_timeline_pattern_bundle_enrichment.py` (`_cell_overlay_from_frame`, enrichment entry) and `lab_timeline_adapter.py` (`equipment_bundle_overlay_from_rows`).
3. Add fallback in enrichment: when overlay lookup fails or `equipment_bundles` empty, collect rows from `map_view.full_cells` with adapter-compatible keys (`x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`).
4. Call `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire`.
5. Preserve existing path when `cell_overlay_json.equipment_bundles` is present (no behavior change).
6. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (reference only, or shared helper extraction)
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- manual verification: Lab timeline frame with map_view-only cells shows equipment-group outline

## Acceptance Criteria

- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.
- [ ] Enrichment path matches adapter fallback semantics.
- [ ] Existing overlay-JSON path unchanged.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Row shape drift between adapter and enrichment — mirror adapter field normalization exactly.
