---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Stop blank recipe graph tiles from sprite manifest storage drift

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

The staff sprite manifest endpoint (`GET /internal/staff/shape-part-sprites/manifest/`) returns every `ShapePartSprite` ORM row for the requested `renderer_version`, emitting `row.image.url` without checking that the backing PNG exists on configured static storage. The recipe graph editor loads this manifest for Canvas2D tile composition; stale or missing files produce 404 image loads and blank tiles with no server-side signal.

## Scope

Filter `shape_part_sprite_manifest` so only rows with a servable backing PNG are included in the JSON `sprites` map. This directly fixes blank tiles caused by DB/storage drift.

## Non-goals

- Re-baking sprites automatically during manifest requests
- Changing sprite key format or `renderer_version` semantics
- Recipe graph editor client retry logic

## Implementation Plan

1. Read `django_apps/web/views/staff_shared.py` (`shape_part_sprite_manifest`, lines 72–85).
2. Introduce or import a shared `sprite_row_has_stored_image(row) -> bool` helper (see Mid plan).
3. In the manifest loop, skip rows where the helper returns `False`.
4. Preserve existing JSON shape for included rows: `{url, width, height}` per `sprite_key`.
5. Manually verify: create a row with missing storage file → key absent from manifest; valid row still present.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/services/shape_part_sprite_generation.py` (shared helper source)
- `frontend/recipe_graph_editor/index.html` (consumer; read-only)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: N/A
- manual verification: Staff manifest omits keys whose PNG is missing on storage; recipe graph editor no longer 404-loads stale URLs for omitted keys

## Acceptance Criteria

- [ ] Manifest omits rows without backing PNG on storage
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Operators lose visibility into stale DB rows unless optional `skipped_stale_count` is added (Low plan).
- Storage `exists()` may raise `OSError`; helper must fail closed (return `False`), matching bake skip-existing behavior.
