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

# Plan: Restore pattern-bundle highlights on map_view-only timeline frames

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only reads `cell_overlay_json.equipment_bundles`. Renderable frames with miners in `map_view.full_cells` but no overlay JSON ship without `metrics.pattern_bundle_highlights`, so the Lab client omits equipment-group coloring/outline.

## Scope

Ensure enrichment emits `pattern_bundle_highlights` for valid renderable frames that lack `cell_overlay_json`, matching adapter fallback semantics.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights.
- Refactoring the entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics.

## Implementation Plan

1. Reproduce: frame with `map_view.full_cells` containing a miner, empty `metrics`, no `cell_overlay_json` → no highlights today.
2. Read `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame` and `equipment_bundle_overlay_from_rows` as the reference fallback path.
3. In `enrich_lab_timeline_frames_with_pattern_bundle_highlights`, when overlay lookup fails or lacks `equipment_bundles`, collect rows from `map_view.full_cells` (and overlay cells if present) with adapter-compatible keys (`x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`).
4. Reuse `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire` to produce highlights.
5. Verify existing `cell_overlay_json` path is unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (read-only reference)
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py` (read-only reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: n/a
- manual verification: Load Lab timeline frame without overlay JSON; confirm equipment-group outline renders.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Row-shape mismatch between `map_view.full_cells` and adapter overlay rows could produce partial bundles; mirror adapter normalization exactly.
