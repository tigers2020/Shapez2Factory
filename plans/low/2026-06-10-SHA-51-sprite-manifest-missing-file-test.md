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

# Plan: Unit test and optional operator signal for omitted sprite rows

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: Low

## Problem

`test_manifest_json_shape` asserts happy path only; no missing-file case. Operators lack visibility into how many stale rows were skipped.

## Scope

Add unit test for missing storage omission; optionally expose skipped-row count in manifest response for operators.

## Non-goals

- Client retry logic.
- Automatic re-bake.

## Implementation Plan

1. In `tests/unit/web/test_shape_part_sprite.py`, create `ShapePartSprite` row then delete/mock missing storage.
2. Assert manifest JSON omits that sprite key.
3. Optionally add `_meta.skipped_stale_count` (or response header) if spec owners want operator visibility — confirm with issue owner before adding schema fields.
4. Run `pytest tests/unit/web/test_shape_part_sprite.py -v`.

## Files / Areas Likely Affected

- `tests/unit/web/test_shape_part_sprite.py`
- `django_apps/web/views/staff_shared.py` (optional skipped count)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: Test fails when manifest includes missing-storage rows

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Unit regression for missing-file case.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional skipped count is nice-to-have; omit if it expands manifest schema without owner approval.
