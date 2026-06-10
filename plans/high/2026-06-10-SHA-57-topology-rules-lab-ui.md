---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Expose curated topology rules in Lab UI

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: High

## Problem

`lab_page_context()` always supplies `topology_rules: []` despite active `TopologyRule` rows in the database. The Lab topology panel permanently shows empty-state copy even when curated rules exist.

## Scope

Load active topology rules into Lab page context so operators see curated topology guidance in the UI.

## Non-goals

- Populating `extractor_rules` stub
- Changing solver topology validation behavior
- Seeding production topology content

## Implementation Plan

1. Read `django_apps/web/services/asteroid_lab_page_context.py` (`neutral_lab_context`, `lab_page_context`).
2. Read `django_apps/asteroid_lab/services/topology_service.py` and `TopologyRule` model fields.
3. Add helper to load `is_active=True` rules ordered by `sort_order`.
4. Map ORM fields to template contract (`label`, `value`, `detail`).
5. Override `topology_rules` in `lab_page_context()` return value.
6. Verify Lab SSR renders rule list instead of empty-state.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

## Validation Plan

- lint: `ruff check django_apps/web/services/asteroid_lab_page_context.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: N/A
- manual verification: Seeded TopologyRule rows visible in Lab sidebar/modal

## Acceptance Criteria

- [ ] Seeded active topology rules appear in Lab page context
- [ ] Template renders rule list instead of permanent empty-state
- [ ] Solver validation behavior unchanged
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Template expects `.label`/`.value`/`.detail`; mapping from `TopologyRule` fields must be explicit.
