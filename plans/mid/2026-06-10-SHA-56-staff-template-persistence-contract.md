---
linear_issue: SHA-56
title: Recipe graph staff template, bootstrap JSON, and persistence contract
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

# Plan: Staff template/bootstrap wiring and post-0009 persistence contract

## Source Issue

- Linear: SHA-56
- Status at planning time: In Progress
- Priority: Mid

## Problem

Even after a recompute API exists, staff need a Django template that supplies the editor mount contract (`#macro-graph-editor-root`, `#macro-graph-bootstrap`, `#macro-graph-initial-recipe`, `#macro-graph-initial-catalog`) currently only present in `frontend/recipe_graph_editor/index.html` (Vite dev shell). Additionally, migration `0009_drop_pattern_catalog_tables` removed `MacroRecipe` / `graph_document` ORM persistence; save (`commit=true`) has no approved target.

## Scope

1. Create staff page template per editor mount contract in `main.tsx` and `GraphBootstrap` type in `App.tsx`.
2. Populate bootstrap JSON with: `api_recipe_graph_recompute`, `api_shape_part_sprite_manifest`, `csrf_token`, `react_flow_initial`, `react_flow_initial_status`, `macro_step_count`, and staff navigation URLs (`staff_catalog_url`, `staff_recipe_edit_url`) where applicable.
3. Include catalog/recipe JSON script tags the editor reads on boot.
4. Document and implement persistence choice: new model, `game_data` snapshot, or explicit **draft-only** API (no `commit` persistence).

## Non-goals

- Restoring `PatternFamily` / `MacroRecipe` tables without product approval.
- SHA-23/SHA-24 validation fixes.
- SHA-40 CI bundle build enforcement.
- Frontend editor rewrites.

## Implementation Plan

1. Inventory `GraphBootstrap` fields in `frontend/recipe_graph_editor/src/GraphEditor/App.tsx` and script tag IDs in `main.tsx`; treat these as the template contract.
2. Add staff template (e.g. `django_apps/web/templates/web/staff_recipe_graph.html` — exact name TBD) with:
   - `<div id="macro-graph-editor-root">`
   - `<script type="application/json" id="macro-graph-bootstrap">` rendered server-side
   - `<script type="application/json" id="macro-graph-initial-recipe">`
   - `<script type="application/json" id="macro-graph-initial-catalog">`
   - Static includes for `recipe-graph-editor.js` and CSS from `django_apps/web/static/web/js/recipe_graph_editor/`
3. Staff GET view loads initial `react_flow` via `domain_graph_to_react_flow` from an in-memory or session draft document (or empty graph with `react_flow_initial_status: "missing"`).
4. Wire `reverse("web:shape-part-sprite-manifest")` into bootstrap `api_shape_part_sprite_manifest`.
5. **Persistence decision** (human/product):
   - **Option A — draft-only:** API accepts dry-run only; `commit=true` returns `501` or `400` with documented message; no ORM write.
   - **Option B — game_data snapshot:** persist `graph_document` JSON on an existing game-data export model (TBD — confirm model with domain owner).
   - **Option C — new ORM model:** introduce replacement for dropped `MacroRecipe.graph_document` with migration + admin hooks.
6. Record chosen contract in a brief ADR or `documents/ai/` note before implementing `commit=true`.
7. Implement `commit` handler in recompute view only after contract is approved.

## Files / Areas Likely Affected

- `django_apps/web/templates/` (new staff recipe graph template)
- `django_apps/web/views/staff_shared.py` or new staff recipe graph views module
- `django_apps/web/urls.py`
- `django_apps/shapez_solver/migrations/0009_drop_pattern_catalog_tables.py` (reference — do not revert)
- `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py`
- `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` (API flow reference)
- `documents/ai/plan_refactor_priorities_2026-05-06.md` (mentions `test_macro_pattern_staff.py`)

## Validation Plan

- lint: `ruff check django_apps/web/`
- typecheck: `mypy django_apps/web`
- tests: bootstrap field presence covered in Low plan integration tests
- build: none
- manual verification: view page source shows populated bootstrap JSON; sprite manifest URL resolves; editor header links work when URLs provided

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Blocked without product decision:** persistence target after `0009` ORM drop. Default recommendation: ship draft-only first, defer `commit=true` until contract approved.
- Initial recipe/catalog data source after `MacroRecipe` removal is unclear — may need hardcoded seed, session draft, or query against replacement store (TBD).
- `staff_catalog_url` / `staff_recipe_edit_url` may point to removed admin routes; verify or omit until catalog staff UI is restored.
