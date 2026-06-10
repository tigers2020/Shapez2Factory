---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for map_view-only pattern bundle highlights

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`; map_view-only frames are untested.

## Scope

Add unit regression for a renderable frame with `map_view.full_cells` containing equipment (e.g. `fluid_miner`), no `cell_overlay_json`, asserting `metrics.pattern_bundle_highlights` is attached after enrichment.

## Non-goals

- Do not change enrichment implementation (Mid plan).
- Do not add UI tests in this slice.

## Implementation Plan

1. Add test case in `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py` building a minimal renderable frame dict with `map_view.full_cells` miner row and empty `metrics`.
2. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])`.
3. Assert output frame has non-empty `metrics.pattern_bundle_highlights.bundles` matching `build_equipment_bundles(rows)` count.
4. Add companion test confirming existing `cell_overlay_json` path still works unchanged.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py` (reference for expected bundle count)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- typecheck: n/a
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Unit regression added for map_view-only frame.
- [ ] Existing overlay-JSON tests still pass.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Test fixture must satisfy `frame_has_renderable_map` guard used by enrichment.
