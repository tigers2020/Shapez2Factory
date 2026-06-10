---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Unit regression for manifest missing-storage omission

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Low

## Problem

`test_manifest_json_shape` asserts happy path only. No test covers the case where a `ShapePartSprite` row exists but the backing PNG is missing from storage.

## Scope

Add unit test creating a `ShapePartSprite` row then deleting/mocking missing storage; assert manifest omits that key.

## Non-goals

- Integration test against real remote storage.
- Testing every renderer_version variant.

## Implementation Plan

1. Read `tests/unit/web/test_shape_part_sprite.py::test_manifest_json_shape`.
2. Add test: create `ShapePartSprite` with image field pointing to a path, mock `storage.exists` returning `False` (or delete file on local storage).
3. Call manifest endpoint/view helper.
4. Assert the stale key is absent from response JSON.
5. Assert happy-path keys still present for rows with existing files.
6. Run `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`

## Validation Plan

- lint: `ruff check tests/unit/web/test_shape_part_sprite.py`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing first; test will fail until manifest filters by storage existence.
