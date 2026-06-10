---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
  - question
status: planned
created_by: todo-plan-automation
---

# Plan: Recreate recipe graph staff integration tests

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/integration/web/test_macro_pattern_staff.py` is referenced in plans but absent from repo. No integration coverage for bootstrap presence, dry-run JSON shape, or staff auth gate.

## Scope

Recreate integration tests for bootstrap, dry-run, and auth gate.

## Non-goals

- Full browser E2E of React Flow editor.
- Vitest/CI bundle build tests (SHA-40).

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py`.
2. Test staff page renders bootstrap with `api_recipe_graph_recompute` key present.
3. Test POST dry-run returns updated `react_flow` + validation JSON shape.
4. Test unauthenticated request is rejected (staff auth gate).
5. Run `pytest tests/integration/web/test_macro_pattern_staff.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (new)

## Validation Plan

- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing first; tests will fail until staff page and API exist.
