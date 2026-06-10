---
linear_issue: SHA-39
title: game_data browse dashboard omits validate_aggregate_root_inlines errors from staff UI
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Surface aggregate-root inline contract errors on game_data browse dashboard

## Source Issue

- Linear: SHA-39
- Status at planning time: Todo
- Priority: Mid

## Problem

The staff `game_data` browse dashboard calls `validate_section_admin_targets()` and renders `section_errors`, but never invokes or displays `validate_aggregate_root_inlines()`. Aggregate-root ModelAdmin contract drift (missing inlines or `game_data_related_changelists` hook) is only caught by pytest, not in the browse UI staff operators use.

## Scope

Wire `validate_aggregate_root_inlines()` into the browse view context and display its errors in `browse_index.html` alongside existing `section_errors`. Add a focused view-level regression test asserting errors appear in rendered HTML when a spec is violated.

## Non-goals

- Changing `AGGREGATE_ROOT_SPECS` contract contents.
- Refactoring admin inline registration.
- Merging section and aggregate validators into one function.

## Implementation Plan

1. In `django_apps/game_data/browse/views.py`, import `validate_aggregate_root_inlines` from `registry`.
2. Call `aggregate_errors = validate_aggregate_root_inlines()` in `game_data_browse` and pass `aggregate_errors` in the render context (keep separate from `section_errors` for clear messaging).
3. In `django_apps/game_data/templates/admin/game_data/browse_index.html`, extend the existing `messagelist` block to render `aggregate_errors` with the same `errornote` styling as `section_errors` (either a second loop or combined block with distinct prefix such as `Aggregate root:`).
4. Add regression test in `tests/unit/game_data/test_admin_browse.py`: use `monkeypatch` or temporary admin registry manipulation to simulate a missing inline on one aggregate root, GET the browse URL, assert the error string appears in response HTML.
5. Verify happy path unchanged: when `validate_aggregate_root_inlines()` returns `[]`, no extra error blocks render.
6. Run focused tests: `pytest tests/unit/game_data/test_admin_browse.py -v`.

## Files / Areas Likely Affected

- `django_apps/game_data/browse/views.py`
- `django_apps/game_data/browse/registry.py` (read-only; `validate_aggregate_root_inlines` already exists)
- `django_apps/game_data/templates/admin/game_data/browse_index.html`
- `tests/unit/game_data/test_admin_browse.py`

## Validation Plan

- lint: `ruff check django_apps/game_data/browse/views.py`
- typecheck: `mypy django_apps/game_data`
- tests: `pytest tests/unit/game_data/test_admin_browse.py -v`
- build: `python manage.py check`
- manual verification: Staff user opens Game data browse; if aggregate inline contract violated, error appears in messagelist

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Test that simulates violation must restore admin registry state to avoid polluting other tests; prefer monkeypatch on `validate_aggregate_root_inlines` return value for view test, separate parametrize test already covers registry contract.
- Error message density: if both section and aggregate errors exist, UI may show many `errornote` lines; acceptable per spec (mirror existing section_errors pattern).
