---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Implement map_view.full_cells bundle fallback in enrichment

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

Enrichment `_cell_overlay_from_frame` never falls back to `map_view.full_cells` unlike the timeline adapter path.

## Scope

Implement fallback bundle derivation from `map_view.full_cells` mirroring adapter semantics; reuse existing bundle/highlight wire helpers.

## Non-goals

- Changing compose pipeline upstream of enrichment.
- Altering existing overlay-JSON enrichment path.

## Implementation Plan

1. In `_cell_overlay_from_frame`, detect missing or empty `equipment_bundles`.
2. Collect cell rows from `map_view.full_cells` and overlay cells with adapter-compatible shape.
3. Call `equipment_bundle_overlay_from_rows` to build bundles.
4. Emit `metrics.pattern_bundle_highlights` via `build_pattern_bundle_highlights_wire`.
5. Confirm existing overlay-JSON path unchanged (no regression on frames with `cell_overlay_json`).

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Enrichment and adapter must stay in sync if row-shape contract changes; consider shared helper extraction in future refactor (out of scope).
