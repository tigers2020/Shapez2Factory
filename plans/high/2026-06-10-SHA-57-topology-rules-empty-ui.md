---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
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

`lab_page_context()` always supplies `topology_rules: []`. Staff-curated `TopologyRule` rows exist in DB but never reach the Lab topology panel/modal; UI permanently shows empty-state copy even when rules exist.

## Scope

Load active `TopologyRule` rows and map them into `lab_page_context()` for template rendering. Operators should see curated topology guidance in Lab sidebar/modal.

## Non-goals

- Populating `extractor_rules` (separate stub).
- Changing solver topology validation behavior.
- Seeding production topology content (ops task).

## Implementation Plan

1. Read `neutral_lab_context()` and `lab_page_context()` in `asteroid_lab_page_context.py`.
2. Add `list_active_topology_rules_for_lab()` in `topology_service.py` returning template-ready dicts.
3. Map ORM fields: `short_label` → `label`, `title`/severity → `value`, `description` → `detail`.
4. Call helper from `lab_page_context()` after `neutral_lab_context()`, overriding `topology_rules`.
5. Verify template `{% for rule in topology_rules %}` renders list instead of empty-state.
6. Seed test `TopologyRule` rows; load Lab page; confirm rules visible.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- `tests/unit/asteroid_lab/test_topology_service.py`

## Validation Plan

- tests: extend topology service tests or add integration coverage (see Low plan)
- django check: `python manage.py check`
- manual verification: Lab page with seeded rules shows topology list.

## Acceptance Criteria

- [ ] Seeded active topology rules appear in Lab page context.
- [ ] Template renders rule list instead of permanent empty-state.
- [ ] Solver validation behavior unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Template expects `.label`/`.value`/`.detail`; DTO field names must align or template updated.
