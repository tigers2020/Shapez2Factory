---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
  - question
status: planned
created_by: todo-plan-automation
---

# Plan: Restore staff recipe graph editor end-to-end wiring

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: High

## Problem

The React Flow recipe graph editor and `recompute_graph_document` service are implemented, but Django no longer exposes the staff page or HTTP recompute endpoint. Bootstrap `api_recipe_graph_recompute` is never populated. Staff cannot use graph recompute/save.

## Scope

Restore staff page + POST recompute API so the recipe graph editor is functional end-to-end with populated bootstrap JSON.

## Non-goals

- Fixing `validate_graph_document` arity/quantity gaps (SHA-23, SHA-24).
- CI Node build enforcement (SHA-40).
- Restoring dropped `PatternFamily` / `MacroRecipe` tables without approved persistence contract.

## Implementation Plan

1. Read `frontend/recipe_graph_editor/` mount contract (`#macro-graph-editor-root`, `#macro-graph-bootstrap`).
2. Add staff template with bootstrap JSON including `api_recipe_graph_recompute` and `api_shape_part_sprite_manifest`.
3. Add staff-only POST recompute route in `django_apps/web/urls.py` calling `recompute_graph_document`.
4. Wire `reverse()` URL into bootstrap via staff view in `staff_shared.py`.
5. Decide post-0009 persistence target (draft-only vs new model) before commit path.
6. Manually verify editor loads and dry-run recompute succeeds.

## Files / Areas Likely Affected

- `django_apps/web/urls.py`
- `django_apps/web/views/staff_shared.py`
- `django_apps/web/templates/` (new staff recipe graph template)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `frontend/recipe_graph_editor/` (consumer only)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_recipe_graph_recompute.py -v`
- build: `python manage.py check`
- manual verification: Staff page mounts editor with working recompute POST

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Blocked product decision:** post-0009 `graph_document` persistence target must be decided before commit=true path ships.
