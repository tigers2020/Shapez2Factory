---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Expose topology rules catalog in Lab UI

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: High

## Problem

`lab_page_context()` always supplies `topology_rules: []`. Staff-curated `TopologyRule` rows never reach the Lab topology panel/modal, so operators see permanent empty-state copy even when rules exist in the database.

## Scope

Load active topology rules into Lab page context so the template renders curated guidance instead of empty-state.

## Non-goals

- Populating `extractor_rules` (separate stub).
- Changing solver topology validation behavior.
- Seeding production topology content.

## Implementation Plan

1. Read `neutral_lab_context()` in `django_apps/web/services/asteroid_lab_page_context.py` (line 158 hardcoded `[]`).
2. Add `list_active_topology_rules_for_lab()` in `topology_service.py` querying `is_active=True` ordered by `sort_order`.
3. Map ORM fields to template contract: `short_label` → label, `title`/severity → value, `description` → detail.
4. Call helper from `lab_page_context()` after `neutral_lab_context()`.
5. Verify template `{% for rule in topology_rules %}` renders seeded rules.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

## Validation Plan

- lint: `ruff check django_apps/web/services/asteroid_lab_page_context.py django_apps/asteroid_lab/services/topology_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: `python manage.py check`
- manual verification: Seeded topology rules appear in Lab sidebar panel

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Template expects `.label`/`.value`/`.detail`; confirm mapping matches all active rule field shapes.
