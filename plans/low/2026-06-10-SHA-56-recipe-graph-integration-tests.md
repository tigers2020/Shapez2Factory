---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - question
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Integration tests for recipe graph bootstrap, dry-run, and auth gate

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/unit/shapez_solver/test_recipe_graph_recompute.py` covers the service only. `tests/integration/web/test_macro_pattern_staff.py` is referenced in plan docs but absent from the repo. No integration coverage asserts bootstrap presence, dry-run JSON shape, or staff auth gate.

## Scope

Recreate integration tests for bootstrap field presence, POST dry-run response shape, and staff-only auth enforcement.

## Non-goals

- Full browser/E2E React Flow interaction tests.
- SHA-23/SHA-24 validation regression.
- Persistence commit path tests until persistence contract is decided.

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py` (or equivalent path).
2. Assert staff page response includes bootstrap JSON with `api_recipe_graph_recompute` populated.
3. POST dry-run with sample `graph_document`; assert response includes `react_flow` and validation fields.
4. Assert unauthenticated or non-staff requests receive 403/redirect on page and API.
5. If persistence ships: add commit-path test; else skip with documented reason.

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (new)
- `django_apps/web/urls.py` (reference)
- `django_apps/web/templates/` (reference)
- `tests/unit/shapez_solver/test_recipe_graph_recompute.py` (reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`
- build: N/A
- manual verification: Tests fail on current missing wiring; pass after High/Mid implementation

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Integration tests cover bootstrap, dry-run, and auth gate.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Commit-path test deferred until post-0009 persistence decision; document skip reason in test module.
