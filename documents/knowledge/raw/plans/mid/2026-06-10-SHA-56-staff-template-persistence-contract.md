---
linear_issue: SHA-56
title: Recipe graph editor — staff template/bootstrap detail and persistence contract
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
- Status at planning time: Todo
- Priority: Mid

## Problem

Two mid-priority gaps block a complete restore:

1. **Template/bootstrap**: Production Django templates lack `#macro-graph-bootstrap`, catalog/recipe JSON scripts, and static bundle includes that the Vite dev shell (`frontend/recipe_graph_editor/index.html`) provides. Bootstrap never sets `api_recipe_graph_recompute` or related URLs.
2. **Persistence**: Migration `0009_drop_pattern_catalog_tables` removed `MacroRecipe` / `graph_document` ORM storage. The recompute API's `commit=true` path has no approved persistence target (new model, game_data snapshot, or draft-only API).

## Scope

### Template and bootstrap

- Staff template with all mount IDs and JSON script tags matching `main.tsx` / `App.tsx` contracts.
- Bootstrap fields: `api_recipe_graph_recompute`, `api_shape_part_sprite_manifest`, `csrf_token`, `staff_catalog_url`, `staff_recipe_edit_url`, `react_flow_initial`, `react_flow_initial_status`, `macro_step_count`.
- Catalog operation rows and engine operation IDs passed into editor mount props (via template context or embedded JSON).

### Persistence contract

- Document and implement one of:
  - **Draft-only**: `commit=true` returns 501/409 with explicit message; editor works for dry-run only.
  - **New ORM model**: approved schema for `graph_document` JSON storage linked to recipe identity.
  - **game_data snapshot**: persist into existing game_data export/import path.
- Wire `commit=true` in recompute API only after contract is chosen.

## Non-goals

- Restoring dropped `PatternFamily` / `MacroRecipe` tables without explicit approval.
- SHA-23/SHA-24 validation fixes.
- SHA-40 CI bundle enforcement.

## Implementation Plan

1. Inventory historical staff macro views/templates from git history or `documents/ai/plan_refactor_priorities_2026-05-06.md` / `plan_deferred_png_warm_queue.md` for bootstrap field names and URL patterns.
2. Draft persistence ADR or contract brief (`documents/ai/templates/contract-brief.md` format): options, chosen target, acceptance for `commit=true`.
3. If draft-only: implement API branch returning clear JSON error; document in contract brief; update issue comment for human sign-off.
4. If persistence approved: add model/migration or game_data adapter; load initial `graph_document` in page view; persist on `commit=true` in recompute handler.
5. Build staff template extending existing staff base (match nav/shell from other staff pages); embed bootstrap via `json_script` filter or manual `application/json` script tags.
6. Page view: serialize catalog operations (`macro_recipe_staff_catalog` service or successor), initial react_flow via `domain_graph_to_react_flow`, enrichment via `enrich_react_flow_with_macro_visual_previews` on GET.
7. Set `data-shape-part-sprite-manifest-url` on `#macro-graph-editor-root` matching dev shell pattern.
8. Cross-check bootstrap keys against `GraphBootstrap` type in `frontend/recipe_graph_editor/src/GraphEditor/App.tsx`.

## Files / Areas Likely Affected

- `django_apps/web/templates/web/` (new or restored macro graph template)
- `django_apps/web/views/` (staff page view context builder)
- `django_apps/shapez_solver/migrations/` (only if new persistence model approved)
- `django_apps/shapez_solver/models.py` (only if new persistence model approved)
- `documents/ai/` (persistence contract brief / ADR)
- `frontend/recipe_graph_editor/index.html` (dev shell reference)
- `frontend/recipe_graph_editor/src/main.tsx`
- `django_apps/shapez_solver/migrations/0009_drop_pattern_catalog_tables.py` (context for what was removed)

## Validation Plan

- lint: `ruff check django_apps/web django_apps/shapez_solver`
- typecheck: `mypy django_apps/web django_apps/shapez_solver`
- tests: page context unit tests if persistence model added; `python manage.py check`
- build: TBD if template changes require bundle rebuild (SHA-40)
- manual verification: inspect rendered HTML for all bootstrap keys; test `commit=false` dry-run; test `commit=true` per chosen contract

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Staff template renders bootstrap JSON with `api_recipe_graph_recompute` and sprite manifest URL.
- [ ] Persistence contract documented and implemented (or explicit draft-only mode).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Blocked product decision**: persistence target must be resolved before `commit=true` can ship; draft-only is acceptable interim per issue scope.
- Catalog/recipe data source after ORM drop: TBD — may need game_data import or stub recipe for dev.
- `staff_catalog_url` / `staff_recipe_edit_url` may point to removed admin routes; verify against current URL map.
