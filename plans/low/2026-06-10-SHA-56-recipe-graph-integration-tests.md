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

# Plan: Integration tests for recipe graph staff bootstrap and auth

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/integration/web/test_macro_pattern_staff.py` is referenced in plans but absent from the repo; service-only unit tests do not cover Django wiring.

## Scope

Recreate integration tests covering bootstrap presence, dry-run JSON shape, commit path (if implemented), and staff auth gate.

## Non-goals

- Do not duplicate service-level tests in `test_recipe_graph_recompute.py`.
- Do not fix validation bugs (SHA-23, SHA-24).

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py`.
2. Test staff page response includes bootstrap with `api_recipe_graph_recompute`.
3. Test dry-run POST returns expected `react_flow` + validation JSON shape.
4. Test unauthenticated or non-staff requests are rejected.
5. Run `pytest tests/integration/web/test_macro_pattern_staff.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (new)
- `django_apps/web/views/` (test targets)
- `django_apps/web/urls.py` (route names for reverse)

## Validation Plan

- lint: `ruff check tests/integration/web/test_macro_pattern_staff.py`
- typecheck: n/a
- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Integration tests cover dry-run and staff auth.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Commit-path tests depend on Mid-plan persistence decision; may be skipped for draft-only mode with documented reason.
