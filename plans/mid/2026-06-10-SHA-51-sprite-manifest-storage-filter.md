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

# Plan: Shared storage-exists helper for sprite bake and manifest

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Mid

## Problem

The bake pipeline's `_variant_row_exists_with_image` guard checks storage existence for `--skip-existing`, but the manifest endpoint duplicates no equivalent check. Logic is divergent and stale rows slip through manifest serialization.

## Scope

Extract shared `sprite_row_has_stored_image(row) -> bool` used by both generation skip-existing and manifest serialization; filter manifest rows to servable sprites only.

## Non-goals

- Changing bake pipeline output format.
- Adding automatic re-bake on manifest request.

## Implementation Plan

1. Read `_variant_row_exists_with_image` in `django_apps/web/services/shape_part_sprite_generation.py`.
2. Extract `sprite_row_has_stored_image(row) -> bool` checking `image.name` non-empty and `image.storage.exists(name)`.
3. Replace inline logic in `_variant_row_exists_with_image` with shared helper.
4. Use same helper in `shape_part_sprite_manifest` before emitting each manifest entry.
5. Optionally expose skipped stale row count in manifest metadata for operators.
6. Run `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`
- `tests/unit/web/test_shape_part_sprite.py`

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py django_apps/web/services/shape_part_sprite_generation.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Skipped-row count is optional per issue spec; omit if it complicates manifest contract without operator demand.
