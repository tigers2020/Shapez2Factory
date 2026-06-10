---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fallback bundle derivation from map_view.full_cells

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

Enrichment never falls back to equipment rows in `map_view.full_cells`, unlike `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame` which rebuilds bundles via `equipment_bundle_overlay_from_rows`.

## Scope

Align pattern-bundle enrichment with adapter fallback: collect cell rows from `map_view.full_cells` and overlay cells, reuse existing bundle/highlight wire helpers.

## Non-goals

- Do not refactor timeline adapter.
- Do not change L3/L4 segment builders.

## Implementation Plan

1. Read adapter fallback in `lab_timeline_adapter.py` `_cell_overlay_json_for_timeline_lab_frame` (lines ~227–255): row shape uses `x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`.
2. Extend `_cell_overlay_from_frame` or enrichment loop: when overlay lacks `equipment_bundles`, collect rows from serialized `map_view.full_cells` and overlay cells on the frame dict.
3. Call `equipment_bundle_overlay_from_rows(rows)` from `django_apps/asteroid_lab/snapshots/equipment_bundles.py`, then `_wire_from_equipment_bundles` or `build_pattern_bundle_highlights_wire`.
4. Preserve early-exit when `_pattern_bundle_wire_is_usable(metrics)` or overlay JSON already has bundles.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (reference only)
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py` (`equipment_bundle_overlay_from_rows`, `build_equipment_bundles`)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Enrichment path matches adapter fallback semantics.
- [ ] Existing overlay-JSON path unchanged.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Serialized frame `map_view` shape may differ from adapter `ReplayMapView` objects; row extraction must handle dict/list cell entries consistently.
