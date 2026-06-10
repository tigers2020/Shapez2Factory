---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - question
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Staff template, bootstrap JSON, and POST recompute route with persistence decision

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Mid

## Problem

High plan restores page and API wiring; this tier completes the staff template contract, bootstrap field population, and POST recompute route shape per `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` §3.2. Persistence after migration `0009_drop_pattern_catalog_tables` remains undefined — commit path cannot ship without an explicit target.

## Scope

Implement staff template with full bootstrap JSON, POST recompute route (`macro_pattern_staff_api_recipe_graph_recompute` or equivalent), and document or implement post-0009 `graph_document` persistence (or explicit draft-only mode).

## Non-goals

- SHA-23/SHA-24 validation bug fixes.
- Restoring `PatternFamily` / `MacroRecipe` tables without approved contract.
- CI bundle build enforcement (SHA-40).

## Implementation Plan

1. Decide post-0009 persistence target: new model, game_data snapshot, or draft-only API (blocked product decision).
2. Add staff template per DESIGN.md mount contract: `#macro-graph-editor-root`, `#macro-graph-bootstrap`, catalog/recipe JSON script tags, static bundle includes.
3. Implement POST recompute view calling `recompute_graph_document` → `domain_graph_to_react_flow` with validation/visual enrichment; avoid double `validate_graph_document` when using `recompute_validated_graph_document`.
4. Populate bootstrap with `api_recipe_graph_recompute`, `api_shape_part_sprite_manifest` (where used), and `react_flow_initial`.
5. If persistence approved: wire `commit=true` to chosen storage; else return explicit draft-only response and document limitation.

## Files / Areas Likely Affected

- `frontend/recipe_graph_editor/` (`main.tsx`, `useRecipeGraphRecompute.ts`)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py`
- `django_apps/web/urls.py`
- `django_apps/web/views/` (staff recompute view)
- `django_apps/web/templates/` (staff recipe graph template)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_solver/test_recipe_graph_recompute.py -v`
- build: N/A
- manual verification: Bootstrap JSON fields present in page source; POST dry-run and commit (or draft-only) paths behave per persistence decision

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Staff template renders bootstrap with all required fields.
- [ ] POST recompute route returns correct JSON shape.
- [ ] Persistence contract documented and implemented, or explicit draft-only mode stated.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Persistence blocked on product decision for post-0009 `graph_document` storage; commit path may ship as draft-only until resolved.
