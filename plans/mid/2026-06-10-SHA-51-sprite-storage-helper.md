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

# Plan: Shared sprite storage-exists helper

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Mid

## Problem

Bake pipeline uses `_variant_row_exists_with_image` for `--skip-existing` but manifest path duplicates no equivalent check. A shared helper avoids drift.

## Scope

Extract `sprite_row_has_stored_image(row) -> bool` used by both generation skip-existing and manifest serialization.

## Non-goals

- Automatic re-bake on manifest request
- Client-side retry logic

## Implementation Plan

1. Extract helper from `shape_part_sprite_generation._variant_row_exists_with_image` (or generalize it).
2. Use helper in `shape_part_sprite_manifest` filter loop.
3. Use helper in bake `--skip-existing` path if not already centralized.

## Files / Areas Likely Affected

- `django_apps/web/services/shape_part_sprite_generation.py`
- `django_apps/web/views/staff_shared.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: bake skip-existing and manifest agree on row eligibility

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Implement alongside High plan in single PR.
