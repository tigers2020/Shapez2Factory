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

# Plan: Shared sprite_row_has_stored_image helper

## Source Issue

- Linear: SHA-51
- Priority: Mid

## Problem

Bake pipeline uses `_variant_row_exists_with_image` but manifest path does not share the guard.

## Scope

Extract shared helper used by generation skip-existing and manifest serialization.

## Implementation Plan

1. Read `_variant_row_exists_with_image` in `shape_part_sprite_generation.py`.
2. Extract `sprite_row_has_stored_image(row) -> bool` to shared module or same file with export.
3. Use in `shape_part_sprite_manifest` and generation `--skip-existing` path.
4. Run `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`

## Validation Plan

- tests: `test_shape_part_sprite.py`

## Acceptance Criteria

- [ ] Shared helper used by both paths.
- [ ] Happy-path manifest shape unchanged.

## Risks / Open Questions

- Keep helper in services layer, not views.
