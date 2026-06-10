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

# Plan: Prevent blank recipe graph tiles from manifest/storage drift

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

The staff sprite manifest endpoint returns every `ShapePartSprite` ORM row without verifying the backing PNG exists on storage. The recipe graph editor loads this manifest for Canvas2D tiles; stale or missing files produce 404 loads and blank tiles with no server-side signal.

## Scope

Ensure manifest only advertises sprites that are actually servable (DB row and storage file present).

## Non-goals

- Re-baking sprites during manifest requests.
- Changing sprite key format or `renderer_version` semantics.
- Recipe graph editor client retry logic.

## Implementation Plan

1. Trace `shape_part_sprite_manifest` in `staff_shared.py` (lines ~76–84) and confirm unconditional URL emission.
2. Compare with `_variant_row_exists_with_image` guard in `shape_part_sprite_generation.py`.
3. Filter manifest rows to those with non-empty `image.name` and `image.storage.exists(name)`.
4. Verify recipe graph editor receives fewer 404s for stale DB rows.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/shape_part_sprite_generation.py`
- `frontend/recipe_graph_editor/index.html` (read-only — consumer)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: Manifest omits row when storage file deleted

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Manifest omits rows without backing PNG on storage.
- [ ] Happy-path manifest shape unchanged.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Shared helper extraction tracked in Mid plan; single PR preferred.
