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

# Plan: Pattern bundle map_view-only regression test

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

Regression test for map_view-only frame.

## Scope

Add unit regression in `test_lab_timeline_pattern_bundle_enrichment.py` for a renderable frame with `map_view.full_cells` equipment rows but no `cell_overlay_json`, asserting `pattern_bundle_highlights` are attached.

## Non-goals

- Changing L3/L4 segment builders that already attach highlights in metrics.
- Refactoring the entire timeline adapter or compose pipeline.
- UI changes beyond receiving correct metrics on affected frames.

## Implementation Plan

1. Extend `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`.
2. Build minimal frame fixture: renderable `map_view.full_cells` with `fluid_miner` row, empty `metrics`, no `cell_overlay_json`.
3. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights` and assert `metrics.pattern_bundle_highlights` is populated.
4. Cross-check against `build_equipment_bundles(rows)` expected bundle count.
5. Confirm existing overlay-JSON test cases still pass unchanged.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py` (test target reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High/Mid fallback implementation landing first.
- Fixture row shape must match adapter-compatible fields for stable assertions.
