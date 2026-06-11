---
linear_issue: SHA-51
title: shape_part_sprite_manifest lists DB rows without verifying PNG exists on storage
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Fix blank recipe graph tiles from sprite manifest/storage drift

## Source Issue

- Linear: SHA-51
- Status at planning time: Todo
- Priority: High

## Problem

The staff sprite manifest endpoint returns every `ShapePartSprite` ORM row without checking that the backing PNG exists on storage. The recipe graph editor loads this manifest to compose shape tiles; stale or missing files produce 404 image loads and blank tiles with no server-side signal.

## Scope

Ensure manifest only advertises sprites that are actually servable (DB row and storage file present) so recipe graph editor does not receive dead URLs.

## Non-goals

- Re-baking sprites automatically during manifest requests.
- Changing sprite key format or `renderer_version` semantics.
- Recipe graph editor client retry logic.

## Implementation Plan

1. Read `shape_part_sprite_manifest` in `django_apps/web/views/staff_shared.py` (lines 76–84).
2. Identify where `{url, width, height}` entries are emitted without storage check.
3. Filter rows to those with existing storage files before adding to manifest JSON.
4. Verify recipe graph editor (`frontend/recipe_graph_editor/index.html`) no longer receives keys for missing PNGs.
5. Manually test: create DB row without file → key absent from manifest response.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `frontend/recipe_graph_editor/index.html` (consumer only; no edit unless contract changes)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/web/test_shape_part_sprite.py -v`
- build: `python manage.py check`
- manual verification: Manifest omits keys for rows with missing storage files

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Storage backend differences (local vs remote) may affect `exists()` latency; acceptable for manifest endpoint.
