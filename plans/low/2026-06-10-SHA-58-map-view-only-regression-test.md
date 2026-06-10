---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for map_view-only frame (no cell_overlay_json)

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`. The map_view-only gap that caused missing highlights has no regression guard.

## Scope

Add a unit test asserting `enrich_lab_timeline_frames_with_pattern_bundle_highlights` attaches `metrics.pattern_bundle_highlights` when a renderable frame has equipment in `map_view.full_cells` and no `cell_overlay_json`.

## Non-goals

- Changing production enrichment logic (covered by High/Mid plans).
- Broad replay integration or browser E2E tests.
- Testing L3/L4 segment builders.

## Implementation Plan

1. Add `test_enrichment_adds_highlights_from_map_view_full_cells_without_overlay` in `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`.
2. Build frame wire with `_row(-1, 0, "fluid_miner")` in `map_view.full_cells`, empty `metrics`, and **no** `cell_overlay_json` key.
3. Call enrichment; assert `out[0]["metrics"][METRICS_KEY]` is present and `len(highlights["bundles"]) >= 1`.
4. Optionally assert bundle count matches `len(build_equipment_bundles(rows))`.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v` and confirm pass after High/Mid implementation lands.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: `python manage.py check`
- manual verification: N/A (unit test only)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Unit regression added for map_view-only frame.

## Risks / Open Questions

- Test will fail until High/Mid implementation is merged; run order should be implementation first, then test, or TDD with expected red-then-green in same PR.
