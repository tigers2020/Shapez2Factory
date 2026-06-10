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

# Plan: Fallback bundle derivation from map_view.full_cells in enrichment (SHA-58 Mid)

## Source Issue

- Linear: SHA-58
- Status at planning time: In Progress
- Priority: Mid

## Problem

Enrichment never falls back to equipment rows in `map_view.full_cells`, unlike `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame` which rebuilds bundles via `equipment_bundle_overlay_from_rows`.

## Scope

When overlay lookup fails or lacks `equipment_bundles`, collect cell rows from `map_view.full_cells` and overlay cells, reuse `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire`, emit `metrics.pattern_bundle_highlights`.

## Non-goals

- UI changes beyond correct metrics payload.
- Refactoring entire adapter pipeline.

## Implementation Plan

1. Read `enrich_lab_timeline_frames_with_pattern_bundle_highlights` and `_cell_overlay_from_frame` in `lab_timeline_pattern_bundle_enrichment.py`.
2. Mirror adapter fallback from `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame`: gather rows from `map_view.full_cells` when overlay JSON absent.
3. Call `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` from `snapshots/equipment_bundles.py`, then wire highlights via existing helper.
4. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v` to ensure overlay-JSON path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (reference)
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`
- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`

## Acceptance Criteria

- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.
- [ ] Enrichment path matches adapter fallback semantics.
- [ ] Existing overlay-JSON path unchanged.

## Risks / Open Questions

- Only enrich renderable frames; preserve early exits for non-renderable payloads.
