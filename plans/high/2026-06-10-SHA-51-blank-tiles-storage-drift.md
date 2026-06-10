---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - bug
  - ui
  - test
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Fix blank recipe graph tiles from DB/storage drift

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

The staff sprite manifest endpoint (`GET /internal/staff/shape-part-sprites/manifest/`) returns every `ShapePartSprite` ORM row for the requested `renderer_version`, emitting `row.image.url` without checking that the backing PNG file exists on the configured static storage. The recipe graph editor loads this manifest to compose shape tiles in Canvas2D; stale or missing files produce 404 image loads and blank tiles with no server-side signal.

## Scope

Manifest must only advertise sprites that are actually servable (DB row and storage file present). Operators should not see blank tiles from orphaned DB rows without server-side omission.

## Non-goals

- Re-baking sprites automatically during manifest requests.
- Changing sprite key format or `renderer_version` semantics.
- Recipe graph editor client retry logic (may follow separately).

## Implementation Plan

1. Repro: create `ShapePartSprite` row with missing backing file on storage → call manifest endpoint → confirm key still listed (current bug).
2. Extract or reuse storage-exists guard aligned with bake pipeline `_variant_row_exists_with_image`.
3. Filter `shape_part_sprite_manifest` iteration (`staff_shared.py` lines 76–84) to servable rows only.
4. Optionally expose skipped stale row count in manifest JSON for operator signal.
5. Manual verify: recipe graph editor at `frontend/recipe_graph_editor/index.html` loads tiles without 404 blank slots for drifted keys.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py` (`shape_part_sprite_manifest`, lines 76–84)
- `django_apps/web/services/shape_part_sprite_generation.py` (`_variant_row_exists_with_image`)
- `frontend/recipe_graph_editor/index.html` (`data-shape-part-sprite-manifest-url`)
- `tests/unit/web/test_shape_part_sprite.py`

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py django_apps/web/services/shape_part_sprite_generation.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: Manifest GET omits keys whose PNG missing on storage; recipe graph editor tiles render for remaining keys.

## Acceptance Criteria

- [ ] Manifest omits rows without backing PNG on storage.
- [ ] Happy-path manifest shape unchanged for servable rows.
- [ ] Blank tiles from DB-only rows eliminated at manifest source.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `storage.exists()` per row adds latency on large manifests — acceptable for staff endpoint but monitor.
- Client may cache old manifest until reload; server fix does not retroactively fix cached 404 URLs in open editor tabs.
