---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: Unit test missing storage omission in sprite manifest

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/unit/web/test_shape_part_sprite.py::test_manifest_json_shape` asserts happy path only. No test creates a `ShapePartSprite` row then simulates missing storage file and asserts the manifest omits that key — regression would re-list orphaned DB rows.

## Scope

Add unit test: create `ShapePartSprite` row, delete or mock missing storage, assert manifest omits key. Optionally assert skipped-row count when Mid scope adds operator diagnostics.

## Non-goals

- Integration test through recipe graph editor Canvas2D.
- Re-bake pipeline end-to-end test.
- Changing sprite key format.

## Implementation Plan

1. Review `tests/unit/web/test_shape_part_sprite.py` fixtures and `test_manifest_json_shape` assertions.
2. Add test (e.g. `test_manifest_omits_row_without_stored_image`):
   - Create valid `ShapePartSprite` with image on storage; assert key in manifest.
   - Remove backing file or patch `storage.exists` to return false for that name.
   - GET manifest; assert key absent from response JSON.
3. If Mid scope adds skipped count, assert count increments appropriately.
4. Ensure happy-path `test_manifest_json_shape` still passes unchanged.
5. Run: `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`
- `django_apps/web/views/staff_shared.py` (subject under test)
- `django_apps/web/services/shape_part_sprite_generation.py` (`sprite_row_has_stored_image` reference)

## Validation Plan

- lint: `ruff check tests/unit/web/test_shape_part_sprite.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Unit test fails when manifest lists row without stored PNG.
- [ ] Happy-path manifest test still passes.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Mock vs real storage delete affects test portability — follow existing `test_shape_part_sprite.py` storage patterns.
- Depends on Mid scope helper for meaningful omission behavior.
