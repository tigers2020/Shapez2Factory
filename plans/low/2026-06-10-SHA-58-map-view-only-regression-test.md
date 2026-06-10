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

# Plan: map_view-only frame regression test

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`. No regression guards the map_view-only fallback path.

## Scope

Add unit test for renderable frame with `map_view.full_cells` miner row, no `cell_overlay_json`, asserting `pattern_bundle_highlights` attached after enrichment.

## Non-goals

- Integration/browser tests
- Changing production enrichment logic (covered in High/Mid plans)

## Implementation Plan

1. Open `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`.
2. Add fixture frame: renderable, `map_view.full_cells` with `fluid_miner`, empty `metrics`, omit `cell_overlay_json`.
3. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])`.
4. Assert `frame["metrics"]["pattern_bundle_highlights"]` non-empty with expected bundle id/count.
5. Add companion test: frame with valid `cell_overlay_json.equipment_bundles` still passes (no regression).
6. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`

## Acceptance Criteria

- [ ] Unit regression added for map_view-only frame.
- [ ] Matches the source issue spec.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Fixture shape must match real replay frame schema used in Lab client.
