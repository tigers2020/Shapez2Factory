---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing — restore end-to-end staff usability
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

The React Flow recipe graph editor (`frontend/recipe_graph_editor/`, committed bundle `recipe-graph-editor.js`) and server-side `recompute_graph_document` service exist, but Django no longer exposes the staff page or HTTP recompute endpoint. `useRecipeGraphRecompute` reads `bootstrap.api_recipe_graph_recompute`; when empty, dry-run, silent validation, and save all fail with **"Missing recompute API URL in bootstrap."** Staff cannot use graph recompute/save even if the static bundle is loaded manually.

## Scope

Deliver a working staff-only path from browser mount through POST recompute response so the editor can dry-run, validate, and (per persistence decision in mid plan) save graphs.

1. Staff page route and template mounting `#macro-graph-editor-root` with `#macro-graph-bootstrap` JSON.
2. Staff-only POST recompute API calling `validate_graph_document` → `recompute_validated_graph_document` (or `recompute_graph_document` once) → `domain_graph_to_react_flow` → visual enrichment.
3. Bootstrap populated with `api_recipe_graph_recompute`, `api_shape_part_sprite_manifest`, `csrf_token`, and initial React Flow payload fields the editor expects.

## Non-goals

- Fixing `validate_graph_document` arity/quantity gaps (SHA-23, SHA-24).
- CI Node build enforcement (SHA-40).
- Rewriting React editor source.
- Restoring dropped `PatternFamily` / `MacroRecipe` ORM tables without approved persistence contract.

## Implementation Plan

1. Add staff page view (e.g. `macro_pattern_graph`) in `django_apps/web/views/` using `@staff_site_required`; load recipe/catalog context from approved persistence source (see mid plan).
2. Create Django template under `django_apps/web/templates/web/` per DESIGN.md mount contract: `#macro-graph-editor-root` inside `max-w-[1600px]` shell, JSON scripts `#macro-graph-bootstrap`, `#macro-graph-initial-recipe`, catalog operation scripts; include committed `recipe-graph-editor.css` and `recipe-graph-editor.js`.
3. Wire `urls.py` staff page route (e.g. `internal/staff/macro-patterns/recipes/<int:recipe_id>/graph/` or documented historical path — confirm against `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` §3.2).
4. Implement `macro_pattern_staff_api_recipe_graph_recompute` POST handler in `django_apps/web/views/staff_shared.py` (or dedicated staff macro views module): parse JSON body (`graph_document`, `commit` flag), run service pipeline, return `{ react_flow, validation, ... }` JSON.
5. Register recompute route in `django_apps/web/urls.py` (e.g. `internal/staff/macro-patterns/api/recipe-graph/recompute/`); export view from `django_apps/web/views/__init__.py`.
6. Build bootstrap dict in page view with `reverse("web:macro-pattern-staff-api-recipe-graph-recompute")`, `reverse("web:shape-part-sprite-manifest")`, `csrf_token`, `react_flow_initial`, `react_flow_initial_status`, `macro_step_count`.
7. Smoke-test manually: staff login → graph page loads → dry-run POST returns updated `react_flow` without bootstrap error.

## Files / Areas Likely Affected

- `django_apps/web/urls.py`
- `django_apps/web/views/staff_shared.py` (or new staff macro views module)
- `django_apps/web/views/__init__.py`
- `django_apps/web/templates/web/` (new macro graph staff template)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py` (call only; no validation bug fixes)
- `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py`
- `django_apps/shapez_solver/services/macro_recipe_graph_visual.py`
- `django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.js` (include only)
- `frontend/recipe_graph_editor/src/GraphEditor/App.tsx` (bootstrap contract reference)
- `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` (historical API flow reference)

## Validation Plan

- lint: `ruff check django_apps/web`
- typecheck: `mypy django_apps/web`
- tests: deferred to low-priority integration plan; run `python manage.py check`
- build: no frontend rebuild required if using committed bundle
- manual verification: staff page mounts editor; dry-run POST succeeds; bootstrap contains `api_recipe_graph_recompute`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Staff page mounts editor with populated bootstrap including `api_recipe_graph_recompute`.
- [ ] POST recompute returns updated `react_flow` + validation payload.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Post-migration `0009_drop_pattern_catalog_tables` removed `MacroRecipe` ORM — page/API cannot persist until persistence target is decided (mid plan).
- Avoid double `validate_graph_document` + `deepcopy` in API path; prefer `recompute_validated_graph_document` after single validation (per bottleneck report §3.2).
- `commit=true` behavior blocked until persistence contract is approved; implement draft-only mode if decision is deferred.
