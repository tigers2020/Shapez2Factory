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

# Plan: Restore equipment-group coloring on map_view-only timeline frames

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

`enrich_lab_timeline_frames_with_pattern_bundle_highlights` only derives `metrics.pattern_bundle_highlights` from `cell_overlay_json.equipment_bundles`. Renderable frames with miners in `map_view.full_cells` but no overlay JSON ship without pattern-bundle highlights, so Lab equipment-group coloring/outline is missing.

## Scope

Ensure valid renderable timeline frames without `cell_overlay_json` receive `metrics.pattern_bundle_highlights` so the Lab client (`asteroid_miner_layout_lab.js`) can render equipment-group styling.

## Non-goals

- Do not change L3/L4 segment builders that already attach highlights in metrics.
- Do not refactor the entire timeline adapter or compose pipeline.
- Do not change UI beyond receiving correct metrics.

## Implementation Plan

1. Reproduce: renderable frame with `map_view.full_cells` containing `fluid_miner`, empty `metrics`, no `cell_overlay_json`; confirm no `pattern_bundle_highlights`.
2. In `enrich_lab_timeline_frames_with_pattern_bundle_highlights`, when overlay lookup fails or lacks `equipment_bundles`, fall back to map cell rows (see Mid plan).
3. Verify Lab client reads `frame.metrics.pattern_bundle_highlights` and renders outlines for affected frames.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (consumer verification)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps config src`
- tests: unit regression in Low plan
- build: n/a
- manual verification: equipment-group outline visible on map_view-only frames

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Frames with `map_view.full_cells` but no overlay JSON receive `pattern_bundle_highlights`.
- [ ] Existing overlay-JSON path unchanged.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Fallback must mirror adapter semantics to avoid highlight drift between compose and enrichment paths.
