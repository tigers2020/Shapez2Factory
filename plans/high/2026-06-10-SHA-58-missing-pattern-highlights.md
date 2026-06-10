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

# Plan: Restore pattern bundle highlights from map_view

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: High

## Problem

Equipment-group coloring/outline missing on valid frames without `cell_overlay_json`.

## Scope

Align `enrich_lab_timeline_frames_with_pattern_bundle_highlights` with the timeline adapter fallback so renderable frames with equipment in `map_view.full_cells` but no `cell_overlay_json` emit `metrics.pattern_bundle_highlights`.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights in metrics.
- Refactoring the entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics on affected frames.

## Implementation Plan

1. Reproduce: renderable frame with `map_view.full_cells` containing `fluid_miner` and empty `metrics` → confirm no `pattern_bundle_highlights`.
2. Compare `_cell_overlay_from_frame` in `lab_timeline_pattern_bundle_enrichment.py` with `_cell_overlay_json_for_timeline_lab_frame` in `lab_timeline_adapter.py`.
3. When overlay lookup fails or lacks `equipment_bundles`, collect cell rows from `map_view.full_cells` and rebuild bundles via `equipment_bundle_overlay_from_rows` or `build_equipment_bundles`.
4. Emit `metrics.pattern_bundle_highlights` using `build_pattern_bundle_highlights_wire`.
5. Manually verify Lab timeline shows equipment-group coloring on map_view-only frames.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (consumer)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: N/A (unit regression deferred to Low plan)
- build: `python manage.py check`
- manual verification: Lab timeline frame with map_view-only equipment → pattern bundle highlights visible in client

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Row shape mapping (`x`, `y`, `cell_kind`/`kind`, `transport_kind`, `rotation`, `tile_type`) must mirror adapter path exactly.
- Mid plan implements fallback; Low plan adds unit regression.
