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

# Plan: Adapter-aligned bundle fallback helpers

## Source Issue

- Linear: SHA-58
- Status at planning time: Todo
- Priority: Mid

## Problem

Enrichment and adapter duplicate overlay resolution logic; only the adapter rebuilds bundles from map cells. Mid work ensures fallback reuses existing bundle/highlight wire helpers without forking semantics.

## Scope

Extract or reuse shared row collection + `equipment_bundle_overlay_from_rows` path so enrichment and adapter stay aligned.

## Non-goals

- Compose pipeline refactor
- Changing highlight wire schema

## Implementation Plan

1. Compare `_cell_overlay_from_frame` (enrichment) vs `_cell_overlay_json_for_timeline_lab_frame` (adapter) row extraction.
2. Prefer calling `equipment_bundle_overlay_from_rows` from enrichment fallback rather than reimplementing bundle grouping.
3. If duplication is high, extract a small shared function (e.g. `_equipment_bundles_from_map_view_frame`) in enrichment module or shared replay util — keep diff minimal.
4. Wire `build_pattern_bundle_highlights_wire` on derived bundles before attaching to `frame.metrics`.
5. Add unit test asserting fallback output matches adapter output for the same synthetic frame fixture.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_timeline_pattern_bundle_enrichment.py`
- `django_apps/asteroid_lab/replay/lab_timeline_adapter.py`
- `tests/unit/asteroid_lab/test_lab_timeline_pattern_bundle_enrichment.py`

## Validation Plan

- tests: targeted pytest on enrichment module
- typecheck: `mypy django_apps config src`

## Acceptance Criteria

- [ ] Fallback bundle derivation mirrors adapter path.
- [ ] Reuse existing bundle/highlight wire helpers.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Shared helper location: enrichment service vs replay package — follow existing import boundaries per `django-apps.mdc`.
