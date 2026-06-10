---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Fallback bundle derivation from map_view.full_cells mirroring adapter

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

`_cell_overlay_from_frame` in `lab_timeline_pattern_bundle_enrichment.py` does not fall back to `map_view.full_cells` when `cell_overlay_json` is absent. `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame` already rebuilds bundles via `equipment_bundle_overlay_from_rows` — enrichment must align with that path.

## Scope

Implement fallback bundle derivation in `enrich_lab_timeline_frames_with_pattern_bundle_highlights` reusing existing bundle/highlight wire helpers.

## Non-goals

- L3/L4 segment builder changes.
- Full timeline adapter refactor.
- UI client changes.

## Implementation Plan

1. In `enrich_lab_timeline_frames_with_pattern_bundle_highlights`, extend `_cell_overlay_from_frame` (or inline fallback) to detect missing/empty `equipment_bundles`.
2. Collect cell rows from `map_view.full_cells` and overlay cells with adapter-compatible shape.
3. Call `equipment_bundle_overlay_from_rows` from `lab_timeline_adapter.py` or `build_equipment_bundles` from `snapshots/equipment_bundles.py`.
4. Wire output through `build_pattern_bundle_highlights_wire` into `metrics.pattern_bundle_highlights`.
5. Verify frames that already include `cell_overlay_json` behave identically.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py` (reference)
- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: N/A
- manual verification: Compare enrichment output with adapter-built overlay for same frame

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Fallback derivation mirrors adapter semantics.
- [ ] Existing overlay-JSON path unchanged.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Prefer importing adapter helper over duplicating row-collection logic to avoid drift.
