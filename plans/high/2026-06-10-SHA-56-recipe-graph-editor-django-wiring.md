---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: High
labels:
  - ui
  - priority:mid
  - test
  - question
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Restore staff recipe graph editor end-to-end wiring

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: High

## Problem

The React Flow recipe graph editor (`frontend/recipe_graph_editor/`, committed bundle `recipe-graph-editor.js`) and server-side `recompute_graph_document` service exist, but Django no longer exposes the staff page or HTTP recompute endpoint. `useRecipeGraphRecompute` reads `bootstrap.api_recipe_graph_recompute`; when empty it surfaces **"Missing recompute API URL in bootstrap."** Staff cannot dry-run, validate, or save graph documents even if the static bundle is loaded manually.

## Scope

Deliver a functional staff recipe graph editor page with bootstrap JSON including `api_recipe_graph_recompute` and a staff-only POST recompute route that returns updated `react_flow` plus validation.

## Non-goals

- Fixing `validate_graph_document` arity/quantity gaps (SHA-23, SHA-24).
- CI Node build enforcement (SHA-40).
- Rewriting the React editor source.
- Restoring dropped `PatternFamily` / `MacroRecipe` ORM tables without an approved persistence contract.

## Implementation Plan

1. Reproduce: confirm no `#macro-graph-editor-root` / `#macro-graph-bootstrap` in `django_apps/web/templates/**/*.html` and no recompute route in `django_apps/web/urls.py`.
2. Add staff view and URL route for recipe graph page and POST recompute API calling `recompute_graph_document` and `domain_graph_to_react_flow`.
3. Add staff template with editor mount, bootstrap JSON (`api_recipe_graph_recompute`, `react_flow_initial`, catalog scripts), and static bundle includes.
4. Wire `reverse()` URL into bootstrap so `useRecipeGraphRecompute` can POST dry-run and optional commit.
5. Smoke-test staff page mount and dry-run JSON response manually.

## Files / Areas Likely Affected

- `frontend/recipe_graph_editor/` (`App.tsx`, `useRecipeGraphRecompute.ts`, `main.tsx`)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `django_apps/web/urls.py`
- `django_apps/web/views/staff_shared.py` (or new staff view module)
- `django_apps/web/templates/` (staff recipe graph template)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_recipe_graph_recompute.py -v`
- build: N/A
- manual verification: Staff page mounts editor; dry-run POST returns `react_flow` + validation JSON

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Staff page mounts editor with populated bootstrap including `api_recipe_graph_recompute`.
- [ ] POST recompute returns updated `react_flow` + validation.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Post-migration `0009_drop_pattern_catalog_tables` removed `MacroRecipe` / `graph_document` ORM persistence; commit/save target requires product decision before persistence can ship (tracked in Mid plan).
