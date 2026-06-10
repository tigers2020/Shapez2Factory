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

# Plan: Optional modal JSON endpoint and integration regression

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

No integration test asserts Lab SSR includes topology rules; per-rule rich modal content has no HTTP endpoint.

## Scope

Add integration regression that seeded `TopologyRule` rows appear in Lab page context. Optionally wire `get_topology_modal_payload` to a staff JSON endpoint if rich modal HTML is required.

## Non-goals

- Do not change solver validation.
- Do not seed production topology content.

## Implementation Plan

1. Add integration test under `tests/integration/web/` asserting `lab_page_context()` or Lab page response includes seeded topology rules.
2. Optionally add staff JSON endpoint using `get_topology_modal_payload(rule_key)` if template needs async modal fetch.
3. Run `pytest tests/integration/web/ -v -k topology`.

## Files / Areas Likely Affected

- `tests/integration/web/` (new or extended)
- `django_apps/web/views/` (optional modal endpoint)
- `django_apps/asteroid_lab/services/topology_service.py`

## Validation Plan

- lint: `ruff check tests/integration/web/`
- typecheck: n/a
- tests: `pytest tests/integration/web/ -v -k topology`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Regression test added for context keys.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Modal endpoint is optional per issue spec; skip if sidebar list mapping satisfies UX.
