---
linear_issue: SHA-23
title: Recipe graph validate_graph_document skips input-count check for binary operations
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Reject under-connected binary operations in validate_graph_document

## Source Issue

- Linear: SHA-23
- Status at planning time: Todo
- Priority: Mid

## Problem

`_validate_operation_inputs` skips arity checks when input edges < `required_input_count`. Under-connected binary ops pass validation.

## Scope

Raise `ValueError` when `len(sorted_edges) < need`; add regression tests for `stacker`/`merge`.

## Implementation Plan

1. Edit `recipe_graph_input_carrier.py` — remove skip/`continue` on under-connected ops.
2. Mirror recompute error messages.
3. Add tests in `test_recipe_graph_input_carrier.py` for 1-input `stacker`/`merge` rejection.
4. Run `pytest tests/unit/shapez_solver/test_recipe_graph_input_carrier.py -v`.

## Files / Areas Likely Affected

- `django_apps/shapez_solver/services/recipe_graph_input_carrier.py`
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `tests/unit/shapez_solver/test_recipe_graph_input_carrier.py`

## Validation Plan

- tests: targeted pytest above

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low: unify error messages with recompute skip reason.
