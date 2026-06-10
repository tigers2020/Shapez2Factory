---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional modal JSON endpoint and integration regression

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

`get_topology_modal_payload(rule_key)` loads ORM modal content but has no HTTP endpoint. No integration test asserts Lab SSR includes topology rules.

## Scope

Optional per-rule modal JSON endpoint; integration regression that seeded rules appear in Lab page context.

## Non-goals

- Rich modal HTML design changes.
- Solver behavior.

## Implementation Plan

1. If per-rule rich modal required: add staff/public JSON endpoint calling `get_topology_modal_payload(rule_key)`.
2. Add `tests/integration/web/test_lab_topology_rules_context.py`:
   - Seed `TopologyRule(is_active=True, ...)`
   - GET Lab solver page
   - Assert `topology_rules` rendered in HTML or context helper output
3. Run `pytest tests/integration/web/test_lab_topology_rules_context.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/views/` (optional endpoint)
- `django_apps/web/urls.py` (optional)
- `tests/integration/web/test_lab_topology_rules_context.py` (new)

## Validation Plan

- tests: `pytest tests/integration/web/test_lab_topology_rules_context.py -v`

## Acceptance Criteria

- [ ] Regression test added.
- [ ] Optional endpoint only if rich modal content required.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Integration test may use Django test client + template context inspection vs full HTML parse.
