---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Filter sprite manifest to servable PNGs only

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

`shape_part_sprite_manifest` returns every `ShapePartSprite` ORM row emitting `row.image.url` without verifying the backing PNG exists on storage. Recipe graph editor loads manifest for Canvas2D tiles; stale/missing files cause 404 loads and blank tiles with no server-side signal.

## Scope

Omit manifest entries whose `image.name` is empty or `image.storage.exists(name)` is false.

## Non-goals

- Re-baking sprites during manifest requests
- Changing sprite key format or `renderer_version` semantics
- Recipe graph editor client retry logic

## Implementation Plan

1. In `staff_shared.shape_part_sprite_manifest`, filter rows before serialization.
2. Use shared storage-exists check (see Mid plan for helper extraction).
3. Verify happy-path manifest shape unchanged for valid rows.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/shape_part_sprite_generation.py`
- `frontend/recipe_graph_editor/index.html` (consumer, no change expected)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: manifest omits row when storage file deleted

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Storage backend behavior in tests — use mock storage for missing-file case.
