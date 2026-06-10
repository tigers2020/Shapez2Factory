---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing
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

# Plan: Integration tests for recipe graph staff wiring

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/integration/web/test_macro_pattern_staff.py` is referenced in plan docs but absent from the repo. No integration coverage for bootstrap presence, dry-run JSON shape, or staff auth gate.

## Scope

Recreate integration tests covering bootstrap presence, dry-run recompute JSON shape, and staff auth gate.

## Non-goals

- Unit tests for `recompute_graph_document` service (already exist)
- SHA-23/SHA-24 validation regression tests

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py`.
2. Test staff page response includes `#macro-graph-bootstrap` with `api_recipe_graph_recompute` key.
3. Test unauthenticated/non-staff users get 302/403 on page and API.
4. Test dry-run POST returns `react_flow` and validation fields without persisting.
5. Run `pytest tests/integration/web/test_macro_pattern_staff.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (create)

## Validation Plan

- lint: `ruff check tests/integration/web/test_macro_pattern_staff.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Integration tests cover dry-run and staff auth
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Commit-path integration test depends on Mid plan persistence decision.
