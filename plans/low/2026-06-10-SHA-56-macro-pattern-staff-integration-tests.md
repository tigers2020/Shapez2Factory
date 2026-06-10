---
linear_issue: SHA-56
title: Recipe graph editor — integration tests for staff bootstrap and recompute API
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

# Plan: Recreate `test_macro_pattern_staff.py` integration coverage

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Low

## Problem

`tests/integration/web/test_macro_pattern_staff.py` is referenced in plan docs (`documents/ai/plan_refactor_priorities_2026-05-06.md`) but absent from the repo. Without integration tests, bootstrap presence, dry-run JSON shape, staff auth gate, and commit path regressions will not be caught in CI.

## Scope

Recreate integration tests covering:

1. Staff graph page HTML contains `#macro-graph-editor-root`, `#macro-graph-bootstrap`, and populated `api_recipe_graph_recompute` URL.
2. POST recompute dry-run (`commit=false`) returns expected JSON shape (`react_flow`, validation fields).
3. Staff auth gate: anonymous → redirect/login; non-staff → 403.
4. Commit path test aligned with persistence contract from mid plan (skip or xfail if draft-only).

## Non-goals

- Unit tests for `recompute_graph_document` (already in `tests/unit/shapez_solver/test_recipe_graph_recompute.py`).
- Frontend Vitest tests (SHA-40).
- Validation bug fixes (SHA-23, SHA-24).

## Implementation Plan

1. Create `tests/integration/web/test_macro_pattern_staff.py` following patterns from `tests/integration/web/test_web_smoke.py` and other staff integration tests.
2. Add fixtures: staff user, non-staff user, minimal valid `graph_document` payload (reuse fixtures from unit tests).
3. Test GET staff graph page: assert bootstrap JSON parses and contains `api_recipe_graph_recompute` matching `reverse()` URL.
4. Test POST recompute dry-run: staff client POSTs valid document; assert 200, `react_flow` nodes/edges present, validation payload present.
5. Test auth: anonymous GET/POST → login redirect; authenticated non-staff → 403.
6. Test commit path per persistence contract (persist + reload, or assert draft-only error response).
7. Run `pytest tests/integration/web/test_macro_pattern_staff.py -v` and include in fast test suite if appropriate.

## Files / Areas Likely Affected

- `tests/integration/web/test_macro_pattern_staff.py` (create)
- `tests/integration/web/conftest.py` (staff user fixtures, if missing)
- `django_apps/web/urls.py` (route names for reverse assertions)
- `documents/ai/plan_refactor_priorities_2026-05-06.md` (historical verification reference)

## Validation Plan

- lint: `ruff check tests/integration/web/test_macro_pattern_staff.py`
- typecheck: `mypy tests/integration/web/test_macro_pattern_staff.py` (if typed)
- tests: `pytest tests/integration/web/test_macro_pattern_staff.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Integration tests cover dry-run and staff auth gate.
- [ ] Commit path covered or explicitly skipped with documented reason (draft-only).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Tests depend on high/mid implementation landing first; may start as skipped until routes exist.
- Commit test shape depends on persistence contract decision (mid plan).
- May need test recipe/graph_document fixture if ORM persistence is not restored.
