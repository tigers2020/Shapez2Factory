---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Map TopologyRule rows into lab_page_context template contract

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `topology_rules: []`. Template `{% for rule in topology_rules %}` expects objects with `.label`, `.value`, `.detail` but no Python code maps `TopologyRule` fields into that shape.

## Scope

Add `list_active_topology_rules_for_lab()` helper and call from `lab_page_context()`. Align template contract (`label`/`value`/`detail`) with ORM fields (`short_label`, `title`/severity, `description`).

## Non-goals

- Wiring `get_topology_modal_payload` HTTP endpoint (Low plan)
- Solver validation changes

## Implementation Plan

1. Add `list_active_topology_rules_for_lab()` in or beside `topology_service.py`.
2. Return list of dicts or simple namespace objects with `label`, `value`, `detail`.
3. Call from `lab_page_context()` after `neutral_lab_context()`.
4. Confirm template loop renders without template changes if mapping is correct.
5. Run existing topology service unit tests.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: N/A
- manual verification: Context dict contains non-empty `topology_rules` when DB seeded

## Acceptance Criteria

- [ ] Seeded active topology rules appear in Lab page context
- [ ] Template renders rule list instead of permanent empty-state
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- If template contract should use `TopologyRuleSummaryDTO` instead, update template rather than ad-hoc dict mapping.
