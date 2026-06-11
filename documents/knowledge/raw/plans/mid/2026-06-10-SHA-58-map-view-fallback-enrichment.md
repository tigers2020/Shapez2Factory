---
linear_issue: SHA-58
title: Pattern bundle timeline enrichment ignores map_view.full_cells when cell_overlay_json is absent
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add map_view.full_cells fallback to pattern-bundle enrichment

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

Enrichment never falls back to `map_view.full_cells` when `cell_overlay_json` is absent, unlike `lab_timeline_adapter._cell_overlay_json_for_timeline_lab_frame`.

## Scope

Implement fallback bundle derivation from `map_view.full_cells` mirroring the adapter path; reuse existing bundle/highlight wire helpers.

## Non-goals

- Changing L3/L4 segment builders.
- Refactoring the entire timeline adapter.
- UI template/JS changes.

## Implementation Plan

1. Extend `_cell_overlay_from_frame` or add a sibling helper that returns equipment bundles from `map_view.full_cells` when overlay JSON is missing.
2. Call `equipment_bundle_overlay_from_rows` with normalized cell rows (same field mapping as adapter).
3. Pipe bundles through `build_pattern_bundle_highlights_wire` into `frame["metrics"]["pattern_bundle_highlights"]`.
4. Guard: only enrich renderable frames (preserve existing renderability checks).
5. Run existing unit tests to confirm overlay-JSON path unchanged.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `django_apps/asteroid_lab/snapshots/equipment_bundles.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `pytest tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py -v`
- build: n/a
- manual verification: Compare highlights on overlay-JSON vs map_view-only frames for same equipment layout.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High-priority behavioral fix landing first if split across PRs.
