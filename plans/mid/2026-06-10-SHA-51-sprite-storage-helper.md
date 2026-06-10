---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Shared sprite_row_has_stored_image helper for bake and manifest

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Mid

## Problem

The bake pipeline's `_variant_row_exists_with_image` guard checks `image.name` and `image.storage.exists(name)` before skipping re-render, but `shape_part_sprite_manifest` does not use equivalent logic. The two paths can drift, advertising sprites the bake pipeline would treat as incomplete.

## Scope

Extract a small shared `sprite_row_has_stored_image(row) -> bool` used by both generation skip-existing and manifest serialization. Refactor `_variant_row_exists_with_image` to delegate to the shared helper after ORM lookup.

## Non-goals

- Changing bake work-queue semantics beyond delegating to shared helper
- Altering `ShapePartSprite` model fields
- Automatic re-bake on manifest request

## Implementation Plan

1. Read `_variant_row_exists_with_image` in `django_apps/web/services/shape_part_sprite_generation.py` (lines 88–115).
2. Add `sprite_row_has_stored_image(row: ShapePartSprite) -> bool` in the same module (or a small `shape_part_sprite_storage_checks.py` if import cycles arise).
3. Implement: return `False` if `row.image` is falsy or `row.image.name` is empty; else `row.image.storage.exists(name)` with `OSError` caught → `False`.
4. Refactor `_variant_row_exists_with_image` to fetch the row, then call `sprite_row_has_stored_image(row)`.
5. Update `shape_part_sprite_manifest` in `staff_shared.py` to call `sprite_row_has_stored_image(row)` before adding to `sprites` dict.
6. Run focused unit tests to confirm skip-existing behavior unchanged.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`

## Validation Plan

- lint: `ruff check django_apps/web/services/shape_part_sprite_generation.py django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: `--skip-existing` bake still skips rows with stored PNG; manifest uses same predicate

## Acceptance Criteria

- [ ] Shared helper used by generation and manifest paths
- [ ] Manifest omits rows without backing PNG on storage
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Placement: keep helper in `shape_part_sprite_generation.py` unless view-layer import from generation module violates layering; if so, extract to `django_apps/web/services/shape_part_sprites.py` or `shape_part_sprite_storage.py`.
