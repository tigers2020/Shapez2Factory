---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for map_view-only timeline frame highlights

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`. No regression guards the map_view-only path where equipment exists in `map_view.full_cells` but overlay JSON is absent.

## Scope

Add unit regression for a renderable map_view-only frame (no `cell_overlay_json`) asserting `pattern_bundle_highlights` are attached.

## Non-goals

- Golden HTML snapshots.
- L3/L4 segment builder tests.
- UI browser tests.

## Implementation Plan

1. Open `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`.
2. Add fixture: renderable frame with `map_view.full_cells` containing a `fluid_miner` row, empty `metrics`, no `cell_overlay_json`.
3. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights`; assert output includes non-empty `metrics.pattern_bundle_highlights`.
4. Assert highlight count matches `build_equipment_bundles(rows)` for same cell rows.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: N/A
- manual verification: Test fails on current enrichment; passes after Mid implementation

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Unit regression added for map_view-only frame.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Fixture row shape must match production `map_view.full_cells` schema to avoid false green.
