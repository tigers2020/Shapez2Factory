---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Low
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Optional topology modal endpoint and integration regression test

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

`get_topology_modal_payload(rule_key)` has no HTTP/view callers. No integration test asserts Lab SSR includes topology rules from seeded ORM rows.

## Scope

Add integration regression test for `lab_page_context()` topology_rules. Optionally wire staff JSON endpoint for per-rule rich modal content if template needs it.

## Non-goals

- Seeding production topology content.
- Solver validation behavior changes.

## Implementation Plan

1. Add `tests/integration/web/test_lab_topology_context.py` (or extend existing web integration tests).
2. `@pytest.mark.django_db`: create active `TopologyRule` fixture, call `lab_page_context()` or render Lab view, assert `topology_rules` length ≥ 1 and field mapping.
3. If rich modal HTML required by template JS, add staff JSON route calling `get_topology_modal_payload` and register URL in `config/urls.py`.
4. Run `pytest tests/integration/web/test_lab_topology_context.py -v`.

## Files / Areas Likely Affected

- `tests/integration/web/test_lab_topology_context.py` (new)
- `django_apps/web/views/` (optional endpoint)
- `config/urls.py` (optional)

## Validation Plan

- tests: `pytest tests/integration/web/test_lab_topology_context.py -v`
- lint: `ruff check tests/integration/web/`

## Acceptance Criteria

- [ ] Regression test added for topology rules in Lab context.
- [ ] Optional endpoint only if spec requires rich modal (issue marks optional).
- [ ] Matches the source issue spec.

## Risks / Open Questions

- Endpoint may be YAGNI if sidebar list is sufficient for v1.
