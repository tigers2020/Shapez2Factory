---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Extract shared sprite_row_has_stored_image helper for bake and manifest

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Mid

## Problem

Bake pipeline uses `_variant_row_exists_with_image` for `--skip-existing` but manifest serialization duplicates no equivalent check.

## Scope

Extract `sprite_row_has_stored_image(row) -> bool` shared by generation skip-existing and manifest filtering.

## Non-goals

- Automatic re-bake on manifest miss.
- Client-side retry logic.

## Implementation Plan

1. Extract helper from `_variant_row_exists_with_image` logic in `shape_part_sprite_generation.py`.
2. Use helper in `shape_part_sprite_manifest` before emitting `{url, width, height}`.
3. Refactor bake `--skip-existing` path to call the same helper.
4. Keep manifest JSON shape identical for valid rows.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: Bake skip-existing and manifest filtering behave consistently

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Shared helper used by generation and manifest paths.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Storage backend mocking in tests must match Django `FileField.storage.exists` contract.
