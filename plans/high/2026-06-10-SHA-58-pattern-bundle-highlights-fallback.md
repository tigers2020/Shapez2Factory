---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Restore pattern-bundle highlights on map_view-only frames

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only derives highlights from `cell_overlay_json.equipment_bundles`. Frames with equipment in `map_view.full_cells` but no overlay JSON ship without `pattern_bundle_highlights`, breaking equipment-group coloring in the Lab client.

## Scope

Align enrichment with adapter fallback so renderable frames without `cell_overlay_json` still receive `metrics.pattern_bundle_highlights`.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights.
- Refactoring entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics.

## Implementation Plan

1. Read `enrich_lab_timeline_frames_with_pattern_bundle_highlights` in `lab_timeline_pattern_bundle_enrichment.py`.
2. Read adapter fallback `_cell_overlay_json_for_timeline_lab_frame` in `lab_timeline_adapter.py`.
3. When overlay lookup fails or lacks `equipment_bundles`, collect rows from `map_view.full_cells`.
4. Reuse `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire`.
5. Verify Lab client reads `frame.metrics.pattern_bundle_highlights` on affected frames.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: `python manage.py check`
- manual verification: Equipment-group coloring visible on map_view-only frames

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Row shape mapping from `map_view.full_cells` must mirror adapter (`x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`).
