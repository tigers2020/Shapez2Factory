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

`test_manifest_json_shape` covers the happy path only. There is no regression test asserting that manifest omits rows when storage backing is missing. Operators also lack visibility into how many stale DB rows were filtered.

## Scope

Add a unit regression test for missing-storage omission. Optionally expose a `skipped_stale_count` (or similar) field in the manifest JSON for operators.

## Non-goals

- Re-baking sprites automatically during manifest requests
- Changing sprite key format or `renderer_version` semantics
- Recipe graph editor client retry logic

## Implementation Plan

1. Read `test_manifest_json_shape` in `tests/unit/web/test_shape_part_sprite.py` (lines 122–153) as the happy-path template.
2. Add `test_manifest_omits_row_when_storage_file_missing`:
   - Create staff user and `ShapePartSprite` row with valid `image` field under `SHAPE_PART_SPRITE_STATIC_ROOT` override (same fixture pattern as happy path).
   - Delete the backing file from disk **or** mock `row.image.storage.exists` to return false for that row.
   - GET manifest; assert the sprite key is **not** in `data["sprites"]`.
   - Assert happy-path keys (if any other rows present) still have `{url, width, height}` shape.
3. Confirm existing `test_manifest_json_shape` still passes unchanged (happy-path manifest shape preserved).
4. **Optional:** In `shape_part_sprite_manifest`, track count of rows skipped due to missing storage; add `"skipped_stale_count": N` to JSON response. Document in test if implemented; skip if product prefers silent omission only.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`
- `django_apps/web/views/staff_shared.py` (only if optional skipped count is added)

## Validation Plan

- lint: `ruff check tests/unit/web/test_shape_part_sprite.py`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py::test_manifest_omits_row_when_storage_file_missing -v`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py::test_manifest_json_shape -v`
- build: `python manage.py check`
- manual verification: TBD — covered by unit test

## Acceptance Criteria

- [ ] Unit regression for missing-file case
- [ ] Happy-path manifest shape unchanged
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Optional `skipped_stale_count` is not in acceptance criteria as required; implement only if Low scope time permits
- Deleting file vs mocking `storage.exists`: prefer delete-on-disk under tmp_path for integration fidelity; mock acceptable if delete races with Django file handling
