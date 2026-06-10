---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Map TopologyRule rows to lab_page_context template contract

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

Template expects objects with `.label`, `.value`, `.detail` but no Python code maps `TopologyRule` fields into that shape. `get_topology_modal_payload` exists but has zero HTTP callers.

## Scope

Load and map active `TopologyRule` rows into `lab_page_context()` with template contract alignment.

## Non-goals

- Wiring rich modal HTML endpoint unless required.
- Changing `TopologyRule` ORM schema.

## Implementation Plan

1. Read `TopologyRule` model fields and `TopologyRuleSummaryDTO` if present.
2. Implement `list_active_topology_rules_for_lab()` returning list of dicts or named tuples with label/value/detail.
3. Override `topology_rules` key in `lab_page_context()` return dict.
4. Optionally add staff JSON endpoint for `get_topology_modal_payload` per-rule rich content.
5. Extend `test_topology_service.py` with context mapping assertions.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `tests/unit/asteroid_lab/test_topology_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Rich modal content may need separate endpoint; defer unless operators require HTML modals beyond sidebar list.
