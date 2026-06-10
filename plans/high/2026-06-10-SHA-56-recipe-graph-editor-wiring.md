---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing
priority: High
labels:
  - bug
  - ui
  - test
  - question
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Restore staff recipe graph editor end-to-end wiring

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: High

## Problem

The React Flow recipe graph editor and server-side `recompute_graph_document` service exist, but Django no longer exposes the staff page or HTTP recompute endpoint. `bootstrap.api_recipe_graph_recompute` is never populated in production templates, so dry-run, validation, and save all fail with "Missing recompute API URL in bootstrap."

## Scope

Make the staff recipe graph editor functional end-to-end: staff page mount, bootstrap JSON with recompute URL, and POST recompute API returning updated `react_flow` + validation.

## Non-goals

- Fixing validate_graph_document arity/quantity gaps (SHA-23, SHA-24)
- CI Node build enforcement (SHA-40)
- Restoring dropped MacroRecipe tables without approved persistence contract

## Implementation Plan

1. Read `frontend/recipe_graph_editor/main.tsx`, `useRecipeGraphRecompute.ts`, and `django_apps/shapez_solver/services/recipe_graph_recompute.py`.
2. Add staff page template with `#macro-graph-editor-root`, `#macro-graph-bootstrap`, catalog scripts, and static bundle includes per DESIGN.md.
3. Add staff-only POST recompute view and `urls.py` route calling `recompute_graph_document` + `domain_graph_to_react_flow`.
4. Populate bootstrap `api_recipe_graph_recompute` via `reverse()`.
5. Verify editor mounts and dry-run POST succeeds for staff user.

## Files / Areas Likely Affected

- `django_apps/web/templates/` (new or restored staff graph template)
- `django_apps/web/views/staff_shared.py`
- `django_apps/web/urls.py`
- `frontend/recipe_graph_editor/` (read-only consumer contract)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py django_apps/web/urls.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_recipe_graph_recompute.py -v`
- build: N/A
- manual verification: Staff page loads editor; bootstrap contains `api_recipe_graph_recompute`; dry-run returns JSON

## Acceptance Criteria

- [ ] Staff page mounts editor with populated bootstrap including `api_recipe_graph_recompute`
- [ ] POST recompute returns updated `react_flow` + validation
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Post-migration `0009` persistence target for `graph_document` is unresolved (see Mid plan).
