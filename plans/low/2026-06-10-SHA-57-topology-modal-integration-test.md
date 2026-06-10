---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Low
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Optional topology modal JSON endpoint and integration regression

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

`get_topology_modal_payload(rule_key)` exists but has no HTTP callers. `test_topology_service.py` covers service lookup only; no integration test asserts Lab SSR includes topology rules in page context.

## Scope

Add optional per-rule modal JSON endpoint using `get_topology_modal_payload` and integration regression that seeded `TopologyRule` rows appear in Lab page context.

## Non-goals

- `extractor_rules` stub.
- Solver validation behavior changes.
- Production topology content seeding.

## Implementation Plan

1. Add staff/operator JSON endpoint (e.g. `/lab/topology/<rule_key>/modal/`) calling `get_topology_modal_payload`.
2. Wire endpoint URL in template or client only if rich modal content is required beyond SSR list.
3. Add `tests/integration/web/` coverage: seed active `TopologyRule`, GET Lab page, assert `topology_rules` non-empty in context or response body markers.
4. Add endpoint test for valid `rule_key` returns modal payload JSON.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- `django_apps/web/urls.py` (if endpoint added)
- `tests/unit/asteroid_lab/test_topology_service.py`
- `tests/integration/web/` (new or extended)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest tests/integration/web/ -k topology -v`
- build: N/A
- manual verification: Modal endpoint returns rich content for seeded rule key

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Integration regression asserts topology rules in Lab context.
- [ ] Optional modal endpoint documented and tested if implemented.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Modal endpoint is optional; skip if SSR list mapping satisfies operator needs.
