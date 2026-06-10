---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
  - question
status: planned
created_by: todo-plan-automation
---

# Plan: Staff template, bootstrap JSON, and recompute route

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Mid

## Problem

Django templates lack `#macro-graph-editor-root` / `#macro-graph-bootstrap`; `urls.py` has no recompute route; bootstrap URL is never set for production.

## Scope

Restore staff template per DESIGN.md mount contract, wire `reverse()` URL into bootstrap JSON, and add POST recompute route. Document or implement post-0009 `graph_document` persistence target.

## Non-goals

- Do not fix validate_graph_document arity/quantity gaps (SHA-23, SHA-24).
- Do not restore ORM tables without approved contract.

## Implementation Plan

1. Add staff template with `#macro-graph-editor-root`, `#macro-graph-bootstrap`, catalog/recipe JSON scripts, and static bundle includes per `frontend/recipe_graph_editor/DESIGN.md`.
2. Implement `macro_pattern_staff_api_recipe_graph_recompute` view (or equivalent) in `django_apps/web/views/` calling `recompute_validated_graph_document` on pre-validated input to avoid double validation.
3. Register URL in `django_apps/web/urls.py`; inject `api_recipe_graph_recompute` into bootstrap via `reverse()`.
4. Document persistence mode: draft-only API vs commit path with explicit storage target.
5. Run `python manage.py check`.

## Files / Areas Likely Affected

- `django_apps/web/templates/`
- `django_apps/web/views/` (new or extended staff views)
- `django_apps/web/urls.py`
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` (reference)

## Validation Plan

- lint: `ruff check django_apps/web/`
- typecheck: `mypy django_apps config src`
- tests: `python manage.py check`
- build: n/a
- manual verification: bootstrap JSON contains recompute URL on staff page

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Staff template and bootstrap JSON wired.
- [ ] POST recompute route registered and callable.
- [ ] Persistence contract documented.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- `MacroRecipe` ORM removal may require draft-only mode until persistence contract is approved.
