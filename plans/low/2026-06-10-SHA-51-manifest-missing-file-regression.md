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

`test_shape_part_sprite.py::test_manifest_json_shape` asserts happy path only. No test covers DB row present but storage file missing — the exact drift scenario causing blank editor tiles.

## Scope

Add unit test: create `ShapePartSprite` row, mock/delete missing storage, assert manifest omits that key. Optionally assert skipped-row count for operators if implemented.

## Non-goals

- E2E recipe graph editor browser test.

## Implementation Plan

1. Open `tests/unit/web/test_shape_part_sprite.py`.
2. Add `test_manifest_omits_row_without_storage_file`:
   - Create sprite row with image field set to a path.
   - Mock `storage.exists` to return False (or delete file in temp media).
   - GET manifest endpoint.
   - Assert sprite key absent from response JSON.
3. Add companion test: valid storage → key present (regression guard for happy path).
4. Run: `pytest tests/unit/web/test_shape_part_sprite.py::test_manifest_omits_row_without_storage_file -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`

## Validation Plan

- lint: `ruff check tests/unit/web/test_shape_part_sprite.py`
- typecheck: N/A
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Unit regression for missing-file case added.
- [ ] Happy-path manifest shape unchanged.
- [ ] Matches the source issue spec.

## Risks / Open Questions

- Optional skipped-row count is nice-to-have; defer if scope creep.
