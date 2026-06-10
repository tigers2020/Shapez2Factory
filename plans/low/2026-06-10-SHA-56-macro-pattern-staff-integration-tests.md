---
linear_issue: SHA-56
title: Recipe graph staff integration tests (bootstrap, dry-run, auth)
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Recreate macro pattern staff integration tests

## Source Issue

- Linear: SHA-56
- Status at planning time: In Progress
- Priority: Low

## Problem

`tests/integration/web/test_macro_pattern_staff.py` is referenced in plan docs (`documents/ai/plan_refactor_priorities_2026-05-06.md`) but absent from the repo. Without integration tests, staff bootstrap presence, dry-run JSON shape, and auth gates are unguarded.

## Scope

Recreate `tests/integration/web/test_macro_pattern_staff.py` covering:

1. Staff GET graph page renders bootstrap with `api_recipe_graph_recompute` populated.
2. POST recompute dry-run (no `commit`) returns updated `react_flow` and validation fields.
3. Unauthenticated and non-staff users are rejected (redirect/403).
4. Optional: `commit=true` behavior per persistence contract from Mid plan.

## Non-goals

- Unit tests for `recompute_graph_document` (already in `tests/unit/shapez_solver/test_recipe_graph_recompute.py`).
- SHA-23/SHA-24 validation regression tests.
- Playwright/browser E2E (unless explicitly added later).

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py` following patterns from existing web integration tests (e.g. staff auth fixtures in `tests/integration/web/`).
2. Add `test_staff_recipe_graph_page_bootstrap_has_recompute_url`: staff client GET → assert `macro-graph-bootstrap` JSON contains non-empty `api_recipe_graph_recompute`.
3. Add `test_staff_recipe_graph_recompute_dry_run`: staff client POST minimal valid `react_flow` payload → assert `200`, response includes `react_flow` and validation-related keys.
4. Add `test_recipe_graph_recompute_requires_staff`: anonymous GET/POST rejected; authenticated non-staff gets 403.
5. If persistence is draft-only: add `test_recipe_graph_recompute_commit_rejected` asserting explicit error for `commit=true`.
6. Run `pytest tests/integration/web/test_macro_pattern_staff.py -v` and `powershell -File scripts/test_fast.ps1` (or targeted subset if full suite is slow).

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (create)
- `tests/integration/web/conftest.py` (if staff fixtures need extension — TBD)
- `django_apps/web/urls.py` (test targets)
- `django_apps/web/views/staff_shared.py` (test targets)

## Validation Plan

- lint: `ruff check tests/integration/web/test_macro_pattern_staff.py`
- typecheck: `mypy django_apps/web` (if view types change)
- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`
- build: none
- manual verification: none required if integration tests pass

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Tests depend on High/Mid wiring landing first; may need minimal fixture `react_flow` payload aligned with `recipe_graph_react_flow_adapter` expectations.
- If persistence remains draft-only, commit-path tests document rejection rather than ORM persistence.
