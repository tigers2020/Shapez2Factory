---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing — restore staff e2e path
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
- Status at planning time: In Progress (moved from Todo after prior automation pass)
- Priority: High

## Problem

The React Flow recipe graph editor (`frontend/recipe_graph_editor/`, committed bundle `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.js`) and server-side `recompute_graph_document` service exist, but Django exposes no staff page or HTTP recompute endpoint. `useRecipeGraphRecompute` reads `bootstrap.api_recipe_graph_recompute`; when empty it sets global status **"Missing recompute API URL in bootstrap."** Staff cannot dry-run, validate, or save even if the static bundle is loaded manually.

## Scope

Restore the minimum staff-facing surface so the editor mounts and can POST recompute:

1. Staff-only GET page route that renders `#macro-graph-editor-root`, `#macro-graph-bootstrap`, catalog/recipe JSON script tags, and the committed `recipe-graph-editor.js` bundle.
2. Staff-only POST recompute API route (historically `macro_pattern_staff_api_recipe_graph_recompute`) wired in `django_apps/web/urls.py`.
3. Bootstrap JSON must populate `api_recipe_graph_recompute` (and `api_shape_part_sprite_manifest` where sprite tiles are used).

## Non-goals

- Fixing `validate_graph_document` arity/quantity gaps (SHA-23, SHA-24).
- CI Node build enforcement (SHA-40).
- Rewriting the React editor source.
- Restoring dropped `PatternFamily` / `MacroRecipe` ORM tables without an approved persistence contract.

## Implementation Plan

1. Add `macro_pattern_staff_api_recipe_graph_recompute` view in `django_apps/web/views/staff_shared.py` (or a focused `staff_recipe_graph.py` module) using `@staff_site_required` and `@require_http_methods(["POST"])`, mirroring the flow documented in `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` §3.2.
2. Parse POST JSON `{ react_flow, commit?: boolean }`; convert `react_flow` → `graph_document` via existing adapter (`recipe_graph_react_flow_adapter.py`).
3. Call `recompute_graph_document` (or `recompute_validated_graph_document` if input is pre-validated) — avoid double `validate_graph_document` when possible.
4. Enrich response with `domain_graph_to_react_flow`, validation summary, and macro visual previews (`macro_recipe_graph_visual.py` / `enrich_react_flow_with_macro_visual_previews`).
5. For `commit=true`: implement only after persistence contract is chosen (see Mid plan); until then return `400` with explicit `draft_only` message or omit commit support.
6. Register URL in `django_apps/web/urls.py` (e.g. `internal/staff/macro-patterns/api/recipe-graph/recompute/`) and export from `django_apps/web/views/__init__.py`.
7. Add staff GET view + template that sets bootstrap `api_recipe_graph_recompute` via `reverse("web:macro-pattern-staff-api-recipe-graph-recompute")` and `api_shape_part_sprite_manifest` via existing manifest route.
8. Smoke-verify: staff login → page loads editor → Dry-run POST returns JSON with `react_flow` and validation fields.

## Files / Areas Likely Affected

- `django_apps/web/urls.py`
- `django_apps/web/views/staff_shared.py` (or new `django_apps/web/views/staff_recipe_graph.py`)
- `django_apps/web/views/__init__.py`
- `django_apps/web/templates/` (new staff recipe graph template — exact path TBD; follow existing staff template patterns)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py`
- `django_apps/shapez_solver/services/macro_recipe_graph_visual.py`
- `frontend/recipe_graph_editor/src/Hooks/useRecipeGraphRecompute.ts` (contract reference only; no edits unless response shape mismatch)
- `frontend/recipe_graph_editor/src/main.tsx` (mount/bootstrap contract reference)

## Validation Plan

- lint: `ruff check django_apps/web/`
- typecheck: `mypy django_apps/web`
- tests: `python manage.py check`; targeted integration tests deferred to Low plan
- build: none (use committed `recipe-graph-editor.js` bundle)
- manual verification: staff page mounts `#macro-graph-editor-root`; bootstrap contains `api_recipe_graph_recompute`; Dry-run returns updated `react_flow` + validation JSON

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `MacroRecipe` ORM removed in migration `0009_drop_pattern_catalog_tables`; `commit=true` persistence target is unresolved (Mid plan).
- Historical view lived in `django_apps/web/views.py`; current codebase only has `staff_shared.py` graph-preview warm — recompute view must be reintroduced, not moved.
- Double validation (`validate_graph_document` twice per request) is a known perf issue; acceptable for initial wiring but should use pre-validated recompute path when feasible.
