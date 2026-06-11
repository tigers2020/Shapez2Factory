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

# Plan: Wire aggregate-root inline errors into browse dashboard

## Source Issue

- Linear: SHA-39
- Status at planning time: Todo
- Priority: Mid

## Problem

The staff `game_data` browse dashboard surfaces taxonomy section admin-target errors via `validate_section_admin_targets()`, but never calls or displays `validate_aggregate_root_inlines()`. Aggregate-root ModelAdmin contract drift (missing inlines or `game_data_related_changelists` hook) is only caught by pytest, not in the browse UI staff operators actually use.

## Scope

Wire `validate_aggregate_root_inlines()` into the browse view context and display its errors in `browse_index.html` (alongside existing `section_errors`). Optionally add a view-level regression test asserting errors appear in the rendered HTML when a spec is violated.

## Non-goals

- Changing `AGGREGATE_ROOT_SPECS` contract contents.
- Refactoring admin inline registration.
- Merging section and aggregate validators into one function.

## Implementation Plan

1. In `django_apps/game_data/browse/views.py`, call `validate_aggregate_root_inlines()` from `django_apps/game_data/browse/registry.py` (lines 310–329) alongside existing `validate_section_admin_targets()`.
2. Pass `aggregate_errors` (or unified error list with clear prefixes) to template context in `game_data_browse` view.
3. Extend `django_apps/game_data/templates/admin/game_data/browse_index.html` to render aggregate-root errors in the existing `messagelist` block next to `section_errors`.
4. Add focused test in `tests/unit/game_data/test_admin_browse.py` that stubs or simulates a missing inline and asserts the browse page HTML shows the error message.
5. Confirm existing `test_aggregate_root_admin_exposes_expected_subtables` still passes.

## Files / Areas Likely Affected

- `django_apps/game_data/browse/views.py`
- `django_apps/game_data/browse/registry.py` (`validate_aggregate_root_inlines`, `AGGREGATE_ROOT_SPECS`)
- `django_apps/game_data/templates/admin/game_data/browse_index.html`
- `tests/unit/game_data/test_admin_browse.py`

## Validation Plan

- lint: `ruff check django_apps/game_data/browse/`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/game_data/test_admin_browse.py -v`
- build: N/A
- manual verification: Staff browse page shows aggregate-root inline errors when contract violated

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Simulating contract violation in test may require careful mocking of admin registry — prefer fixture that documents expected inline set.
- Error list UX: separate sections vs merged list — keep staff-readable prefixes.
