---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Sprite manifest missing-file unit test

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Low

## Problem

`test_manifest_json_shape` asserts happy path only; no test for ORM row with missing storage file.

## Scope

Add unit test creating `ShapePartSprite` row then simulating missing storage; assert manifest omits that key. Optionally expose skipped stale row count for operators.

## Non-goals

- Client retry logic
- Automatic re-bake

## Implementation Plan

1. Add test case to `tests/unit/web/test_shape_part_sprite.py`.
2. Create row with image field; mock/delete storage; call manifest endpoint.
3. Assert key absent from JSON response.
4. (Optional) Add `skipped_stale_count` field to manifest response for ops visibility.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`
- `django_apps/web/views/staff_shared.py` (optional skipped count)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional skipped count is nice-to-have; defer if scope creep.
