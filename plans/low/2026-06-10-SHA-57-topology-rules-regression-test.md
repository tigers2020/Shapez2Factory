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

# Plan: Topology rules Lab context regression test

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

`test_topology_service.py` covers service lookup only. No integration test asserts Lab SSR includes topology rules from seeded ORM rows.

## Scope

Add optional integration regression test that seeded `TopologyRule` rows appear in Lab page context.

## Non-goals

- Full browser render test of topology modal.
- Seeding production topology data.

## Implementation Plan

1. Add test fixture seeding active `TopologyRule` row(s).
2. Call `lab_page_context()` or render Lab page via Django test client.
3. Assert `topology_rules` in context is non-empty with expected label/value/detail.
4. Run `pytest tests/integration/web/ -k topology -v` or extend unit test file.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_topology_service.py`
- `tests/integration/web/` (optional new test)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan landing first.
