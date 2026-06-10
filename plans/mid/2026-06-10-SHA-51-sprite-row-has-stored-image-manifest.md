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

# Plan: Shared sprite_row_has_stored_image helper and manifest filter

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Mid

## Problem

`shape_part_sprite_manifest` iterates `ShapePartSprite.objects.filter(renderer_version=...)` and always adds `{url, width, height}` from the DB row. Bake pipeline `--skip-existing` uses `_variant_row_exists_with_image` guard, but manifest serialization has no equivalent check — DB/storage drift surfaces only as client 404s.

## Scope

Extract shared `sprite_row_has_stored_image(row) -> bool` used by both generation skip-existing and manifest serialization. Filter manifest rows to servable sprites only (`image.name` non-empty and `image.storage.exists(name)`).

## Non-goals

- Re-baking sprites during manifest requests.
- Changing sprite key format or `renderer_version` semantics.
- Recipe graph editor client retry logic.

## Implementation Plan

1. In `shape_part_sprite_generation.py`, extract `sprite_row_has_stored_image(row) -> bool` from `_variant_row_exists_with_image` logic (empty name → false; else `row.image.storage.exists(row.image.name)`).
2. Refactor `_variant_row_exists_with_image` to delegate to shared helper (preserve `--skip-existing` behavior).
3. In `staff_shared.py` `shape_part_sprite_manifest` (lines 76–84), skip rows where `not sprite_row_has_stored_image(row)`.
4. Optionally accumulate skipped count for operator diagnostics in manifest JSON response.
5. Confirm happy-path manifest keys/urls unchanged when storage file present.
6. Run `pytest tests/unit/web/test_shape_part_sprite.py::test_manifest_json_shape -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py` (`_variant_row_exists_with_image`, new `sprite_row_has_stored_image`)
- `django_apps/web/views/staff_shared.py` (`shape_part_sprite_manifest`)
- `tests/unit/web/test_shape_part_sprite.py` (`test_manifest_json_shape`)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py django_apps/web/services/shape_part_sprite_generation.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: Manifest omits drifted row; bake `--skip-existing` behavior unchanged.

## Acceptance Criteria

- [ ] Shared helper used by generation skip-existing and manifest paths.
- [ ] Manifest filters to rows with stored PNG.
- [ ] Happy-path manifest shape unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Helper must use same storage backend as runtime serving (default file storage vs S3).
- Skipped-row count field is optional — document if omitted to avoid API drift.
