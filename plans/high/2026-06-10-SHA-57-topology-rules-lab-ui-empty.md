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

# Plan: Surface curated topology rules in Lab UI

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: High

## Problem

`lab_page_context()` always supplies `topology_rules: []` via `neutral_lab_context()`. Staff-curated `TopologyRule` rows exist in the database but the Lab topology panel/modal permanently shows empty-state copy.

## Scope

End-to-end fix so active topology rules render in the Lab solver page topology panel. Depends on Mid plan for context wiring and field mapping.

## Non-goals

- Populating `extractor_rules`.
- Changing solver topology validation behavior.
- Seeding production topology content.

## Implementation Plan

1. After Mid wiring lands, seed test `TopologyRule` rows (`is_active=True`) in regression test DB.
2. Load Lab page (or call `lab_page_context()` in test) and assert `topology_rules` is non-empty.
3. Verify template `{% for rule in topology_rules %}` renders list items with `label`, `value`, `detail` instead of empty-state block.
4. Manual check: staff topology rules visible in Lab sidebar/modal when DB has active rows.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py tests/integration/web/ -k topology -v` (after Low plan adds coverage)
- manual verification: Lab page with seeded rules shows topology list

## Acceptance Criteria

- [ ] Seeded active topology rules appear in Lab page context.
- [ ] Template renders rule list instead of permanent empty-state.
- [ ] Solver validation behavior unchanged.
- [ ] Matches the source issue spec.

## Risks / Open Questions

- Template expects `.label`/`.value`/`.detail` attributes; mapping must match ORM field names.
