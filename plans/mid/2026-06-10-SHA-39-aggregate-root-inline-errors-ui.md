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

# Plan: Surface aggregate-root inline errors on game_data browse dashboard

## Source Issue

- Linear: SHA-39
- Status at planning time: Todo
- Priority: Mid

## Problem

Staff `game_data` browse dashboard calls `validate_section_admin_targets()` but never `validate_aggregate_root_inlines()`. Aggregate-root ModelAdmin contract drift is only caught by pytest, not the UI operators use.

## Scope

Wire `validate_aggregate_root_inlines()` into browse view context and display errors in `browse_index.html`. Add view-level regression test when inline contract is violated.

## Non-goals

- Changing `AGGREGATE_ROOT_SPECS` contract contents.
- Refactoring admin inline registration.
- Merging section and aggregate validators into one function.

## Implementation Plan

1. In `game_data_browse`, call `validate_aggregate_root_inlines()`; pass `aggregate_errors` to template.
2. Extend `browse_index.html` messagelist to render aggregate-root errors alongside `section_errors`.
3. Add test stubbing missing inline; assert error appears in rendered HTML.
4. Run `pytest tests/unit/game_data/test_admin_browse.py -v`.

## Files / Areas Likely Affected

- `django_apps/game_data/browse/views.py`
- `django_apps/game_data/browse/registry.py`
- `django_apps/game_data/templates/admin/game_data/browse_index.html`
- `tests/unit/game_data/test_admin_browse.py`

## Validation Plan

- tests: `python -m pytest tests/unit/game_data/test_admin_browse.py -v`
- manual verification: browse dashboard shows aggregate-root errors when contract violated

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Error message prefixes should distinguish section vs aggregate errors for operators.
