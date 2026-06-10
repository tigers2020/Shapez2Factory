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

# Plan: full_cells fallback for pattern bundle enrichment

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

Fallback bundle derivation from `map_view.full_cells` mirroring adapter path; reuse existing bundle/highlight wire helpers.

## Scope

Implement the `map_view.full_cells` fallback in `enrich_lab_timeline_frames_with_pattern_bundle_highlights` when `cell_overlay_json` is absent or lacks `equipment_bundles`, reusing the same helpers as `lab_timeline_adapter`.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights in metrics.
- Refactoring the entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics on affected frames.

## Implementation Plan

1. In `_cell_overlay_from_frame` / `enrich_lab_timeline_frames_with_pattern_bundle_highlights`, detect missing or empty `equipment_bundles`.
2. Collect cell rows from `map_view.full_cells` and overlay cells with adapter-compatible row shape.
3. Call `equipment_bundle_overlay_from_rows` or `build_equipment_bundles` + `build_pattern_bundle_highlights_wire`.
4. Attach resulting `pattern_bundle_highlights` to `frame.metrics` without altering the existing overlay-JSON path.
5. Confirm `asteroid_miner_layout_lab.js` consumer reads `frame.metrics.pattern_bundle_highlights` unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (`equipment_bundle_overlay_from_rows`)
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py` (`build_equipment_bundles`)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: `python manage.py check`
- manual verification: map_view-only frame enrichment produces highlights wire

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlaps High plan — implement together in one PR if practical.
- Low plan adds dedicated map_view-only regression test case.
