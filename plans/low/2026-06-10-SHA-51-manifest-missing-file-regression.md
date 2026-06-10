---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test and optional skipped-row count for sprite manifest

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Low

## Problem

`test_manifest_json_shape` asserts the happy path only. There is no unit test proving the manifest omits keys when storage backing is missing. Operators also have no server-side count of skipped stale rows.

## Scope

Add a unit regression test for missing-storage omission. Optionally expose `skipped_stale_count` in manifest JSON for operators.

## Non-goals

- Changing happy-path manifest JSON shape for valid sprites
- Client-side retry logic in recipe graph editor
- Automatic sprite re-bake

## Implementation Plan

1. Read `tests/unit/web/test_shape_part_sprite.py` (`test_manifest_json_shape`, lines 122–153).
2. Add `test_manifest_omits_row_when_storage_file_missing`:
   - Create staff user and `ShapePartSprite` row with valid PNG via `ContentFile`.
   - Create second row with `image` field pointing at a name with no file on storage (mock `storage.exists` → `False`, or delete file after save).
   - GET manifest; assert valid key present, stale key absent.
3. Confirm `test_manifest_json_shape` still passes unchanged.
4. (Optional) If scope allows, add `skipped_stale_count: int` to manifest response when rows are filtered; document in test.
5. Run `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`
- `django_apps/web/views/staff_shared.py` (only if optional `skipped_stale_count` added)

## Validation Plan

- lint: `ruff check tests/unit/web/test_shape_part_sprite.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: N/A (covered by unit test)

## Acceptance Criteria

- [ ] Unit regression for missing-file case
- [ ] Happy-path manifest shape unchanged
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- `skipped_stale_count` is optional per issue spec; omit if it expands contract beyond acceptance criteria.
- Mocking `storage.exists` vs deleting physical file: prefer pattern consistent with existing tests in this file.
