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

# Plan: Restore pattern-bundle highlights on map_view-only timeline frames (SHA-58 High)

## Source Issue

- Linear: SHA-58
- Status at planning time: In Progress
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only reads `cell_overlay_json.equipment_bundles`. Frames renderable with miners in `map_view.full_cells` but without `cell_overlay_json` ship without `metrics.pattern_bundle_highlights`, so Lab equipment-group coloring/outline is missing.

## Scope

User-visible fix: affected timeline frames must include pattern-bundle highlights. Mid plan implements adapter-aligned fallback derivation.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights.
- Full timeline adapter or compose pipeline refactor.

## Implementation Plan

1. Reproduce with renderable frame: `map_view.full_cells` contains `fluid_miner`, empty `metrics` → no highlights today.
2. After Mid fix, same frame includes `pattern_bundle_highlights` consumed by `asteroid_miner_layout_lab.js`.
3. Confirm existing overlay-JSON path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

## Validation Plan

- manual verification: Lab timeline frame without overlay JSON shows equipment-group coloring
- tests: unit regression in Low plan

## Acceptance Criteria

- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.
- [ ] Enrichment path matches adapter fallback semantics.

## Risks / Open Questions

- Row shape passed to bundle builder must match adapter (`x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`).
