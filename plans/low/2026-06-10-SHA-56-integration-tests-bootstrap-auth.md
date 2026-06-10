---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Low
labels:
  - bug
  - ui
  - test
  - question
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Recreate integration tests for bootstrap, dry-run, and auth gate

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/integration/web/test_macro_pattern_staff.py` referenced in plans but absent from repo. No integration coverage for bootstrap presence, dry-run JSON shape, or staff auth gate.

## Scope

Recreate integration tests covering staff page bootstrap, dry-run recompute response shape, and non-staff 403.

## Non-goals

- Frontend Vitest tests (SHA-40).
- Service-only unit tests (already exist in `test_recipe_graph_recompute.py`).

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py`.
2. Test staff GET page contains `api_recipe_graph_recompute` in bootstrap JSON script.
3. Test staff POST dry-run with minimal `graph_document` returns 200, keys `react_flow` and validation fields.
4. Test anonymous/non-staff POST returns 403 or redirect.
5. If `commit=true` implemented, add separate test with persistence assertion.
6. Run `pytest tests/integration/web/test_macro_pattern_staff.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (new)
- `django_apps/web/views/` (under test)
- `django_apps/web/urls.py` (under test)

## Validation Plan

- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`
- lint: `ruff check tests/integration/web/test_macro_pattern_staff.py`

## Acceptance Criteria

- [ ] Integration tests cover dry-run and staff auth.
- [ ] Bootstrap presence asserted in SSR HTML.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Test fixtures need staff user and minimal valid `graph_document`; reuse from `tests/unit/shapez_solver/test_recipe_graph_recompute.py`.
