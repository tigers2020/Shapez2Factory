---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing
priority: Mid
labels:
  - bug
  - ui
  - test
  - question
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Staff template, bootstrap JSON, and recompute route

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Mid

## Problem

Django templates lack `#macro-graph-bootstrap` JSON and `urls.py` has no recipe-graph recompute route. The documented `macro_pattern_staff_api_recipe_graph_recompute` flow exists in notes but not in current views/tests.

## Scope

Restore staff template, bootstrap JSON fields (`api_recipe_graph_recompute`, `react_flow_initial`, catalog scripts), and POST recompute route mirroring `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` §3.2. Document or implement post-0009 `graph_document` persistence target.

## Non-goals

- SHA-23/SHA-24 validation fixes
- Rewriting React editor source
- Restoring PatternFamily/MacroRecipe ORM without contract

## Implementation Plan

1. Review `recipe_graph_bottleneck_report_2026-05-04.md` §3.2 for historical API contract.
2. Implement `macro_pattern_staff_api_recipe_graph_recompute` view in `staff_shared.py` with staff auth gate.
3. Register URL in `django_apps/web/urls.py`.
4. Create staff template wiring bootstrap JSON including `api_shape_part_sprite_manifest` where used.
5. Decide persistence: draft-only API vs new model vs game_data snapshot; document in view or ADR.
6. Avoid double `validate_graph_document` when using `recompute_validated_graph_document`.

## Files / Areas Likely Affected

- `django_apps/web/views/staff_shared.py`
- `django_apps/web/urls.py`
- `django_apps/web/templates/`
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` (reference)

## Validation Plan

- lint: `ruff check django_apps/web/`
- typecheck: `mypy django_apps config src`
- tests: service unit tests + new integration tests (Low plan)
- build: N/A
- manual verification: Bootstrap JSON shape matches frontend `RecipeGraphBootstrap` type

## Acceptance Criteria

- [ ] Persistence contract documented and implemented (or explicit draft-only mode)
- [ ] Staff page mounts editor with populated bootstrap
- [ ] POST recompute returns updated `react_flow` + validation
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Human decision required on post-0009 persistence before `commit=true` path is safe.
