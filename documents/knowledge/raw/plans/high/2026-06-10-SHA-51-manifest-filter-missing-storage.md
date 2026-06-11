---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Filter sprite manifest to servable PNGs only

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

The staff sprite manifest endpoint (`GET /internal/staff/shape-part-sprites/manifest/`) returns every `ShapePartSprite` ORM row for the requested `renderer_version`, emitting `row.image.url` without checking that the backing PNG exists on configured static storage. The recipe graph editor loads this manifest for Canvas2D tile composition; stale or missing files produce 404 image loads and blank tiles with no server-side signal.

## Scope

Update `shape_part_sprite_manifest` to omit rows whose backing PNG is not present on storage. Only advertise sprites that are actually servable (DB row **and** `image.storage.exists(name)` true).

## Non-goals

- Re-baking sprites automatically during manifest requests
- Changing sprite key format or `renderer_version` semantics
- Recipe graph editor client retry logic

## Implementation Plan

1. Read `shape_part_sprite_manifest` in `django_apps/web/views/staff_shared.py` (lines 72–85) and confirm it currently adds every queryset row unconditionally.
2. Introduce or reuse a shared `sprite_row_has_stored_image(row) -> bool` helper (see Mid plan) that returns false when `image.name` is empty or `image.storage.exists(name)` is false (mirror `_variant_row_exists_with_image` guard logic).
3. In `shape_part_sprite_manifest`, iterate queryset rows and only add entries where `sprite_row_has_stored_image(row)` is true.
4. Preserve existing JSON shape for included rows: `{url, width, height}` keyed by `sprite_key`; top-level keys `renderer_version` and `sprites` unchanged.
5. Manually verify recipe graph editor no longer receives URLs for rows with missing storage files.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/shape_part_sprite_generation.py` (shared helper extraction — coordinated with Mid plan)
- `frontend/recipe_graph_editor/index.html` (consumer only; no changes expected)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py django_apps/web/services/shape_part_sprite_generation.py`
- typecheck: `mypy django_apps/web/views/staff_shared.py django_apps/web/services/shape_part_sprite_generation.py`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: Create `ShapePartSprite` row with missing storage file; confirm manifest omits that key and recipe graph tiles do not 404 for it

## Acceptance Criteria

- [ ] Manifest omits rows without backing PNG on storage
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Manifest silently omits stale rows; operators may not notice drift unless skipped-count telemetry (Low plan) is added
- `storage.exists()` per row adds I/O on large manifests; acceptable for staff-only endpoint but worth noting
