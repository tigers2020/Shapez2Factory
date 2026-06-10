---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
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

The React Flow recipe graph editor and `recompute_graph_document` service are implemented, but Django no longer exposes the staff page or HTTP recompute endpoint. `bootstrap.api_recipe_graph_recompute` is never populated; staff cannot use graph recompute/save.

## Scope

Restore Django staff wiring: page template with bootstrap JSON, staff-only POST recompute API, and `api_recipe_graph_recompute` URL in bootstrap. Clarify persistence target after `MacroRecipe` ORM removal (0009).

## Non-goals

- Fixing `validate_graph_document` arity/quantity gaps (SHA-23, SHA-24).
- CI Node build enforcement (SHA-40).
- Removing or rewriting React editor source.
- Restoring dropped `PatternFamily` / `MacroRecipe` tables without approved persistence contract.

## Implementation Plan

1. Read `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` §3.2 for documented API flow.
2. Product decision: post-0009 `graph_document` persistence (new model, game_data snapshot, or draft-only API).
3. Add staff view + `urls.py` route for POST recompute calling `recompute_graph_document`, `domain_graph_to_react_flow`, validation enrichment.
4. Add staff template with `#macro-graph-editor-root`, `#macro-graph-bootstrap`, catalog/recipe JSON scripts, `recipe-graph-editor.js` include.
5. Wire `reverse()` URL into bootstrap `api_recipe_graph_recompute`.
6. Verify dry-run and optional `commit=true` paths return `react_flow` + validation JSON.
7. Smoke: staff page mounts editor without "Missing recompute API URL" error.

## Files / Areas Likely Affected

- `django_apps/web/urls.py`
- `django_apps/web/views/staff_shared.py` (or new staff view module)
- `django_apps/web/templates/` (new staff graph page)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `frontend/recipe_graph_editor/` (reference; bootstrap contract)

## Validation Plan

- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v` (see Low plan)
- lint: `ruff check django_apps/web/views/ django_apps/web/urls.py`
- manual verification: Staff page loads; dry-run POST returns updated `react_flow`.

## Acceptance Criteria

- [ ] Staff page mounts editor with populated bootstrap including `api_recipe_graph_recompute`.
- [ ] POST recompute returns updated `react_flow` + validation.
- [ ] Persistence contract documented and implemented (or explicit draft-only mode).
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- **BLOCKED** until persistence target decided post-migration 0009; may ship draft-only recompute first.
