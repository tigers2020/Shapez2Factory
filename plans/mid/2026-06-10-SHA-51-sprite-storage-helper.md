---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Shared sprite_row_has_stored_image helper for bake and manifest

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Mid

## Problem

`shape_part_sprite_generation.py` has `_variant_row_exists_with_image` for bake `--skip-existing`, but `shape_part_sprite_manifest` does not reuse it. Manifest serialization and generation skip logic can drift.

## Scope

Extract shared `sprite_row_has_stored_image(row) -> bool` used by generation skip-existing and manifest serialization. Filter manifest rows to servable sprites only.

## Non-goals

- Automatic re-bake on manifest request.
- Client-side retry logic.

## Implementation Plan

1. Read `_variant_row_exists_with_image` in `shape_part_sprite_generation.py`.
2. Extract public helper `sprite_row_has_stored_image(row: ShapePartSprite) -> bool`:
   - Return False if `not row.image.name`
   - Return `row.image.storage.exists(row.image.name)`
3. Replace internal bake guard call with shared helper.
4. In `shape_part_sprite_manifest`, skip rows where helper returns False.
5. Optionally log or expose skipped stale row count for operators (Low plan).
6. Run: `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py django_apps/web/services/shape_part_sprite_generation.py`
- typecheck: `mypy django_apps/web/views/staff_shared.py`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: manifest JSON excludes missing-storage keys

## Acceptance Criteria

- [ ] Shared helper used by generation and manifest paths.
- [ ] Manifest omits rows without backing PNG.
- [ ] Matches the source issue spec.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Storage backend mock in tests must match Django file field behavior.
