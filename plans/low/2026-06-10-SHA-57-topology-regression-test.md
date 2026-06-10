---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Topology rules Lab context regression test and optional modal endpoint

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

`test_topology_service.py` covers service lookup only. No integration test asserts Lab SSR includes topology rules. `get_topology_modal_payload` has zero view/URL callers.

## Scope

Add regression coverage that seeded `TopologyRule` rows appear in Lab page context. Optionally wire per-rule modal JSON endpoint.

## Non-goals

- Seeding production topology content
- Changing solver validation

## Implementation Plan

1. Extend `test_topology_service.py` or add `tests/integration/web/test_lab_topology_context.py`.
2. Seed active `TopologyRule` row; call `lab_page_context()` or GET Lab page.
3. Assert `topology_rules` non-empty with expected label/value/detail.
4. (Optional) Add staff JSON endpoint using `get_topology_modal_payload(rule_key)`.
5. Run focused pytest.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_topology_service.py` or `tests/integration/web/` (new)
- `django_apps/web/views/` (only if optional modal endpoint added)
- `django_apps/web/urls.py` (only if optional modal endpoint added)

## Validation Plan

- lint: `ruff check tests/`
- typecheck: `mypy django_apps config src`
- tests: focused pytest on topology context
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Regression test added
- [ ] Solver validation behavior unchanged
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed
- [ ] Remaining risks are reported

## Risks / Open Questions

- Modal endpoint is optional per issue spec; skip if High/Mid scope is sufficient.
