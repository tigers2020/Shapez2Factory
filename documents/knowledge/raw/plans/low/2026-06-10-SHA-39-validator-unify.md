---
linear_issue: SHA-39
title: game_data browse dashboard omits validate_aggregate_root_inlines errors from staff UI
priority: Low
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unify browse validators (SHA-39 Low)

## Source Issue

- Linear: SHA-39
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid plan wires `validate_aggregate_root_inlines()` into the browse view, staff UI will display two parallel validator outputs (`section_errors` and `aggregate_errors`). Refactoring validators into a unified function would reduce duplication and simplify template rendering but is explicitly deferred from Mid scope.

## Scope

- Optional refactor merging `validate_section_admin_targets()` and `validate_aggregate_root_inlines()` behind a single browse validation API.
- Unified error shape for template rendering.

## Non-goals

- Changing `AGGREGATE_ROOT_SPECS` contract contents.
- Mid plan browse UI wiring.
- Admin inline registration changes.

## Implementation Plan

1. After Mid plan lands, review error shapes from `django_apps/game_data/browse/registry.py` for both validators.
2. Introduce `validate_browse_contract()` (or similar) returning structured errors with `source` field (`section` vs `aggregate_root`).
3. Update `django_apps/game_data/browse/views.py` to call unified validator; simplify `browse_index.html` to iterate one error collection.
4. Preserve existing pytest coverage in `tests/unit/game_data/test_admin_browse.py` — migrate assertions to unified API.

## Files / Areas Likely Affected

- `django_apps/game_data/browse/registry.py`
- `django_apps/game_data/browse/views.py`
- `django_apps/game_data/templates/admin/game_data/browse_index.html`
- `tests/unit/game_data/test_admin_browse.py`

## Validation Plan

- lint: `ruff check django_apps/game_data/browse/`
- typecheck: spot-check if unified error types added
- tests: `pytest tests/unit/game_data/test_admin_browse.py -v`
- build: N/A
- manual verification: Browse page shows same errors as before refactor

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing first.
- Unified refactor is cosmetic — defer if Mid wiring is sufficient for operators.
