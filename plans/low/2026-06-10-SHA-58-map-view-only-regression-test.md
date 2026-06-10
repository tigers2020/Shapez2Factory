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

# Plan: Regression test for map_view-only frame enrichment

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Low

## Problem

`test_lab_timeline_pattern_bundle_enrichment.py` only covers frames that already include `cell_overlay_json`. No test for map_view-only frames.

## Scope

Add unit regression: renderable frame with `map_view.full_cells` miner row, no `cell_overlay_json`, asserts `pattern_bundle_highlights` attached.

## Non-goals

- Integration/Lab browser tests.
- Adapter changes beyond what Mid plan requires.

## Implementation Plan

1. Open `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`.
2. Add fixture frame:

```python
frame = {
    "map_view": {
        "full_cells": [
            {"x": 0, "y": 0, "cell_kind": "fluid_miner", "transport_kind": "belt", ...}
        ]
    },
    "metrics": {},
}
```

3. Call `enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])`.
4. Assert `result[0]["metrics"]["pattern_bundle_highlights"]` non-empty; bundle count matches `build_equipment_bundles` expectation.
5. Run `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py::test_enrich_map_view_only_frame -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`

## Acceptance Criteria

- [ ] Unit regression added for map_view-only frame.
- [ ] Test fails before fix, passes after.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Frame must be "renderable" per enrichment guards; check `is_renderable_lab_timeline_frame` preconditions.
