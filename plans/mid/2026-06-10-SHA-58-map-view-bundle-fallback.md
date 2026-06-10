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

# Plan: Fallback bundle derivation from map_view.full_cells mirroring adapter path

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

Pattern-bundle enrichment and the timeline adapter disagree on how to obtain equipment bundles when `cell_overlay_json` is absent. The adapter rebuilds from `map_view.full_cells` and `overlay_cells`; enrichment stops without emitting highlights.

## Scope

Align enrichment fallback with `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame`: collect rows from renderable map cells, rebuild bundles via shared helpers, wire highlights through existing metrics path.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights in metrics.
- Refactoring the entire timeline adapter or compose pipeline.
- Introducing a second bundle-building algorithm divergent from `equipment_bundle_overlay_from_rows`.

## Implementation Plan

1. Study `_cell_overlay_json_for_timeline_lab_frame` in `lab_timeline_adapter.py` (lines ~227–255): row collection, dedupe by `(x, y)`, field mapping from `ReplayCell` to dict rows.
2. Extract or reuse a shared helper (prefer import of `equipment_bundle_overlay_from_rows` from `django_apps/asteroid_lab/snapshots/equipment_bundles.py`) rather than duplicating bundle logic in enrichment.
3. Add `_rows_from_map_view(frame)` (or equivalent) in `lab_timeline_pattern_bundle_enrichment.py` that reads `map_view.full_cells` and overlay cells from frame wire (dict or nested `frame_payload`), normalizing `cell_kind`/`kind` and `transport_kind`/`transport`.
4. When overlay JSON is missing or `equipment_bundles` is empty, call `equipment_bundle_overlay_from_rows(rows)` and pass resulting bundles through `_wire_from_equipment_bundles`.
5. Confirm existing overlay-JSON path in `_cell_overlay_from_frame` → `_wire_from_equipment_bundles` is unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py` (`equipment_bundle_overlay_from_rows`, `build_equipment_bundles`)
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (reference implementation)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: `python manage.py check`
- manual verification: Compare bundle count from enrichment vs adapter for the same frame wire.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Enrichment path matches adapter fallback semantics.
- [ ] Existing overlay-JSON path unchanged.

## Risks / Open Questions

- Whether to extract shared row-collection into a small module used by both adapter and enrichment (optional; avoid scope creep unless duplication is large).
- `frame_payload` nesting for `map_view` must be handled consistently with `_cell_overlay_from_frame`.
