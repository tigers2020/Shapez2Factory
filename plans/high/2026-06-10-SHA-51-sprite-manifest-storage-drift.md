---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fix blank recipe graph tiles from sprite manifest/storage drift

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

The staff sprite manifest endpoint returns every `ShapePartSprite` ORM row without verifying the backing PNG exists on storage. The recipe graph editor loads this manifest for Canvas2D tiles; stale or missing files produce 404 image loads and blank tiles with no server-side signal.

## Scope

Ensure manifest only advertises sprites that are actually servable (DB row and storage file present). Operators should not see blank tiles from orphaned DB rows.

## Non-goals

- Re-baking sprites during manifest requests.
- Changing sprite key format or renderer_version semantics.
- Recipe graph editor client retry logic.

## Implementation Plan

1. Read `shape_part_sprite_manifest` in `django_apps/web/views/staff_shared.py` (~76–84).
2. Filter rows through shared storage-exists guard (Mid plan).
3. Verify recipe graph editor manifest load no longer receives URLs for missing files.
4. Run unit tests including missing-file regression (Low plan).

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/shape_part_sprite_generation.py`
- `frontend/recipe_graph_editor/index.html` (consumer, verify only)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps/web/views/staff_shared.py`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: manifest with orphaned DB row omits key; editor tiles render for valid sprites

## Acceptance Criteria

- [ ] Manifest omits rows without backing PNG on storage.
- [ ] Matches the source issue spec.
- [ ] Happy-path manifest shape unchanged for valid rows.

## Risks / Open Questions

- Depends on Mid plan shared helper extraction.
