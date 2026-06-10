---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fallback bundle derivation from map_view.full_cells

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

`_cell_overlay_from_frame` in enrichment module does not fall back to `map_view.full_cells` unlike adapter's `_cell_overlay_json_for_timeline_lab_frame`.

## Scope

Implement fallback in `enrich_lab_timeline_frames_with_pattern_bundle_highlights` reusing existing bundle/highlight wire helpers.

## Non-goals

- Adapter refactor.
- Compose pipeline changes.

## Implementation Plan

1. Update `_cell_overlay_from_frame` or inline fallback in enrichment loop.
2. Collect cell rows from `map_view.full_cells` and overlay cells with fields: `x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`.
3. Reuse `equipment_bundle_overlay_from_rows` from `lab_timeline_adapter.py`.
4. Pass bundles through `build_pattern_bundle_highlights_wire`.
5. Write highlights into `metrics.pattern_bundle_highlights` only when not already present.
6. Run existing enrichment tests to confirm overlay-JSON path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`

## Acceptance Criteria

- [ ] Fallback mirrors adapter semantics.
- [ ] Existing overlay-JSON path unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Import cycle risk if enrichment imports adapter directly; may extract shared helper to neutral module.
