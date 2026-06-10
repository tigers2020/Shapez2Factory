---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
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

The React Flow recipe graph editor and `recompute_graph_document` service exist, but Django no longer exposes the staff page or HTTP recompute endpoint. Bootstrap never sets `api_recipe_graph_recompute`, so dry-run, validation, and save fail with "Missing recompute API URL in bootstrap."

## Scope

Make the staff recipe graph editor functional end-to-end: staff page mount, bootstrap JSON with recompute URL, and POST recompute API returning updated `react_flow` plus validation.

## Non-goals

- Do not fix SHA-23/SHA-24 validation gaps.
- Do not enforce CI Node build (SHA-40).
- Do not remove or rewrite the React editor source.
- Do not restore dropped `PatternFamily` / `MacroRecipe` tables without an approved persistence contract.

## Implementation Plan

1. Confirm post-migration-0009 persistence target for `graph_document` (draft-only vs new model vs game_data snapshot).
2. Add staff view and `urls.py` route for recipe graph page with `#macro-graph-editor-root` and `#macro-graph-bootstrap`.
3. Add staff-only POST recompute endpoint calling `recompute_graph_document`, `domain_graph_to_react_flow`, and validation/visual enrichment per `recipe_graph_bottleneck_report_2026-05-04.md` §3.2.
4. Populate bootstrap JSON with `api_recipe_graph_recompute` and `api_shape_part_sprite_manifest` where used.
5. Smoke-test staff page: editor mounts, dry-run POST succeeds.

## Files / Areas Likely Affected

- `django_apps/web/urls.py`
- `django_apps/web/views/staff_shared.py` (or new staff view module)
- `django_apps/web/templates/` (new staff template)
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `frontend/recipe_graph_editor/` (bootstrap contract reference only)

## Validation Plan

- lint: `ruff check django_apps/web/`
- typecheck: `mypy django_apps config src`
- tests: integration tests in Low plan
- build: n/a
- manual verification: staff page loads editor; dry-run POST returns JSON

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Staff page mounts editor with populated bootstrap including `api_recipe_graph_recompute`.
- [ ] POST recompute returns updated `react_flow` + validation.
- [ ] Persistence contract documented and implemented (or explicit draft-only mode).
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Persistence target after `0009_drop_pattern_catalog_tables` is a product decision; implementation may be blocked until decided.
