---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: High
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Surface curated topology rules in Asteroid Lab UI

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: High

## Problem

The Asteroid Lab solver page renders a Topology Constraints modal and sidebar panel from `topology_rules`, but `lab_page_context()` always supplies an empty list via `neutral_lab_context()`. Staff-curated `TopologyRule` / `TopologyRuleModalContent` rows exist in the database but never reach the template, so operators permanently see empty-state copy ("Run Solver to generate constraints") even when rules are seeded.

## Scope

Make active `TopologyRule` rows visible in the Lab topology panel/modal so operators receive curated topology guidance from the database.

## Non-goals

- Populating `extractor_rules` (separate stub; no ORM/service yet).
- Changing solver topology validation behavior.
- Seeding production topology content (ops/data task).

## Implementation Plan

1. Reproduce: seed active `TopologyRule` rows; confirm Lab page `topology_rules` context is `[]`.
2. Load active rules (`is_active=True`, ordered by `sort_order`) in `lab_page_context()`.
3. Map ORM fields to template contract (`label`, `value`, `detail`) expected by `{% for rule in topology_rules %}`.
4. Verify template renders rule list instead of permanent empty-state.
5. Confirm solver validation behavior unchanged.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: N/A
- manual verification: Lab page with seeded rules shows topology panel entries

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Seeded active topology rules appear in Lab page context.
- [ ] Template renders rule list instead of permanent empty-state.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Field mapping (`short_label` → label, `title`/severity → value, `description` → detail) must match template contract; Mid plan owns helper extraction.
