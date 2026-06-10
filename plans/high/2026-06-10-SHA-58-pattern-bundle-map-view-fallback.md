---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Restore equipment-group coloring for map_view-only timeline frames

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only derives `metrics.pattern_bundle_highlights` from `cell_overlay_json.equipment_bundles`. It never falls back to equipment rows in `map_view.full_cells`, unlike `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame`. Timeline frames renderable with miners in `map_view.full_cells` but without `cell_overlay_json` ship without highlights; the Lab client (`asteroid_miner_layout_lab.js`) reads `frame.metrics.pattern_bundle_highlights`, so equipment-group coloring/outline is missing.

## Scope

Ensure frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights` in metrics.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights in metrics.
- Refactoring the entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics on affected frames.

## Implementation Plan

1. Reproduce: renderable frame with `fluid_miner` in `map_view.full_cells`, empty `metrics`, no `cell_overlay_json` → no highlights; `build_equipment_bundles(rows)` returns one bundle.
2. When overlay lookup fails or lacks `equipment_bundles`, collect cell rows from `map_view.full_cells` and overlay cells.
3. Reuse `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire` (mirror adapter path).
4. Emit `metrics.pattern_bundle_highlights` on enriched frames.
5. Confirm existing overlay-JSON path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: N/A
- manual verification: Lab timeline frame without overlay JSON shows equipment-group coloring

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.
- [ ] Enrichment path matches adapter fallback semantics.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Row shape for fallback (`x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`) must match adapter expectations.
