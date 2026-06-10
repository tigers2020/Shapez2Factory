---
linear_issue: SHA-24
title: Recipe graph validate_graph_document accepts non-integer quantity; macro visual truncates via int()
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Enforce integer quantity in validate_graph_document

## Source Issue

- Linear: SHA-24
- Status at planning time: Todo
- Priority: Mid

## Problem

Float quantities pass validation; macro visual silently truncates via `int()`. `validate_recipe_graph_context` rejects non-integers but is test-only.

## Scope

Reuse/extract quantity integer check into `validate_graph_document` production path; reject floats.

## Implementation Plan

1. Read `recipe_graph_recipe_validation.py` and `validate_recipe_graph_context` quantity logic.
2. Extract shared helper; call from `validate_graph_document` in `recipe_graph_recompute.py`.
3. Add `test_validate_graph_document_rejects_float_quantity`.
4. Run `pytest tests/unit/shapez_solver/test_recipe_graph_recipe_validation.py -v`.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `django_apps/shapez_solver/services/macro_recipe_graph_visual.py`
- `django_apps/shapez_solver/services/recipe_graph_recipe_validation.py`
- `tests/unit/shapez_solver/test_recipe_graph_recipe_validation.py`

## Validation Plan

- tests: targeted pytest

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low: document rounding policy if product wants different behavior.
