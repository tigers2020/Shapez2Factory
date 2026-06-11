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

The bake pipeline's `--skip-existing` path uses `_variant_row_exists_with_image` to check DB row + storage presence, but the manifest endpoint does not. This duplication risks drift when storage-check logic changes in one path only.

## Scope

Extract a small shared `sprite_row_has_stored_image(row) -> bool` helper used by both `_variant_row_exists_with_image` (generation skip-existing) and `shape_part_sprite_manifest` serialization. Refactor `_variant_row_exists_with_image` to delegate to the shared helper after fetching the row.

## Non-goals

- Re-baking sprites automatically during manifest requests
- Changing sprite key format or `renderer_version` semantics
- Recipe graph editor client retry logic

## Implementation Plan

1. Read `_variant_row_exists_with_image` in `django_apps/web/services/shape_part_sprite_generation.py` (lines 88–115); note it checks `row.image.name`, then `row.image.storage.exists(name)`, with `OSError` guard returning false.
2. Add `sprite_row_has_stored_image(row: ShapePartSprite) -> bool` in the same module (or a small `shape_part_sprites` utility if that module already owns sprite contracts — follow existing import patterns).
3. Implement helper: empty/missing `image.name` → false; `storage.exists(name)` with `OSError` → false; otherwise true.
4. Refactor `_variant_row_exists_with_image` to fetch row by variant keys, then call `sprite_row_has_stored_image(row)` when row is not None.
5. Import and use `sprite_row_has_stored_image` in `shape_part_sprite_manifest` (`staff_shared.py`) to filter manifest entries.
6. Run existing generation tests to confirm `--skip-existing` behavior unchanged.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/shape_part_sprites.py` (only if helper placement fits existing conventions)

## Validation Plan

- lint: `ruff check django_apps/web/services/shape_part_sprite_generation.py django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps/web/services/shape_part_sprite_generation.py django_apps/web/views/staff_shared.py`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: Run sprite bake with `--skip-existing` on a variant that already has storage; confirm skip count unchanged

## Acceptance Criteria

- [ ] Shared helper used by generation and manifest paths
- [ ] Manifest omits rows without backing PNG on storage
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Helper placement: prefer `shape_part_sprite_generation.py` near `_variant_row_exists_with_image` unless `shape_part_sprites.py` already exports similar guards
- View importing from generation service is acceptable in this codebase pattern; avoid circular imports
