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

# Plan: Unit test and optional skipped-row count for sprite manifest

## Source Issue

- Linear: SHA-51
- Priority: Low

## Problem

`test_manifest_json_shape` covers happy path only; no missing-file case.

## Scope

Add regression test; optionally expose skipped stale row count for operators.

## Implementation Plan

1. Add `test_manifest_omits_row_without_storage_file` in `test_shape_part_sprite.py`.
2. Create `ShapePartSprite` row, mock/delete storage file, GET manifest, assert key absent.
3. Optional: add `skipped_stale_count` field to manifest JSON for operator visibility.
4. Run `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`
- `django_apps/web/views/staff_shared.py` (optional count field)

## Validation Plan

- tests: new regression test

## Acceptance Criteria

- [ ] Missing storage case covered by unit test.

## Risks / Open Questions

- Skipped count is optional per issue spec.
