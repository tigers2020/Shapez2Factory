# planner_rules.py refactoring plan

Date: 2026-05-02

## Goals

- Consolidate repeated operation solution assembly code in `planner_rules.py` into helpers.
- Thin rule function bodies so only “which rule” is visible.

## Change scope

- `django_apps/shapez_solver/services/planner_rules.py`
- planner-related tests if needed

## Approach

1. Add internal helper reading operation catalog defaults.
2. Add single-input and binary-input operation solution helpers.
3. Refactor rotation and cutter derivatives to use same helpers.
4. Split cut-from-source derivative candidate collection into helper.
5. Verify planner unit tests, types, and lint.

## Expected benefits

- Shorter rule functions with clearer intent.
- Single place to edit operation recipe creation logic.
- Easier future split into rule-object form.
