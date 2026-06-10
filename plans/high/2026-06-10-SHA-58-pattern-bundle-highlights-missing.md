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

# Plan: Equipment-group coloring/outline missing on valid frames without cell_overlay_json

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only derives `metrics.pattern_bundle_highlights` from `cell_overlay_json.equipment_bundles` (or an existing metrics wire). It never falls back to equipment rows in `map_view.full_cells`, unlike `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame`, which rebuilds bundles from map cells via `equipment_bundle_overlay_from_rows`.

Timeline frames that are renderable and contain miners in `map_view.full_cells` but omit `cell_overlay_json` therefore ship without pattern-bundle highlights. The Lab client reads `frame.metrics.pattern_bundle_highlights` (`asteroid_miner_layout_lab.js`), so equipment-group coloring/outline can be missing on those frames.

## Scope

Restore correct `metrics.pattern_bundle_highlights` on renderable timeline frames that have equipment in `map_view.full_cells` but no usable overlay JSON. User-visible equipment-group coloring and outline must appear on affected replay frames.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights in metrics.
- Refactoring the entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics on affected frames.

## Implementation Plan

1. Reproduce the bug: build a renderable frame with `map_view.full_cells` containing a `fluid_miner` row, empty `metrics`, and no `cell_overlay_json`; confirm enrichment returns no `pattern_bundle_highlights` while `build_equipment_bundles(rows)` returns at least one bundle.
2. In `enrich_lab_timeline_frames_with_pattern_bundle_highlights`, after overlay lookup fails or lacks `equipment_bundles`, collect cell rows from `map_view.full_cells` and overlay cells (mirror adapter row shape: `x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`).
3. Call `equipment_bundle_overlay_from_rows` (or `build_equipment_bundles` + existing `_wire_from_equipment_bundles`) to derive bundles, then attach `metrics.pattern_bundle_highlights` when bundles exist.
4. Preserve existing behavior when `cell_overlay_json.equipment_bundles` is present or metrics already carry a usable wire.
5. Manually verify Lab replay shows equipment-group outline on a frame that previously lacked highlights.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (reference for fallback semantics)
- `django_apps/asteroid_lab/static/asteroid_lab/js/asteroid_miner_layout_lab.js` (consumer; read-only unless contract mismatch)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: `python manage.py check`
- manual verification: Load a replay frame with map_view-only miners; confirm equipment-group coloring/outline renders.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.

## Risks / Open Questions

- Row deduplication between `full_cells` and overlay cells must match adapter `seen` set semantics to avoid duplicate bundle keys.
- Frames with partial or malformed cell rows should fail closed (no highlights) rather than raise during enrichment.
