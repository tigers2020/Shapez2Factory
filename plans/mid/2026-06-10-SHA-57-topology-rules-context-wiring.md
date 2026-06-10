---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Mid
labels:
  - ui
  - priority:mid
  - test
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Load and map active TopologyRule rows in lab_page_context()

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `"topology_rules": []` and `lab_page_context()` never overrides it. `get_topology_modal_payload(rule_key)` loads ORM rows but has zero view/URL callers. Template expects `.label`, `.value`, `.detail` but no Python code maps `TopologyRule` fields into that shape.

## Scope

Add a dedicated helper to load and map active `TopologyRule` rows, call it from `lab_page_context()`, and align template contract.

## Non-goals

- `extractor_rules` wiring.
- Solver topology validation changes.
- Production content seeding.

## Implementation Plan

1. Add `list_active_topology_rules_for_lab()` in `topology_service.py` returning template-ready dicts (`short_label` → label, `title` or severity → value, `description` → detail).
2. Call helper from `lab_page_context()` after `neutral_lab_context()` to override `topology_rules`.
3. Verify `asteroid_miner_layout_solver.html` `{% for rule in topology_rules %}` renders mapped fields without template changes (or update template if DTO fields differ).
4. Extend `test_topology_service.py` with mapping coverage for active/inactive and sort order.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- `tests/unit/asteroid_lab/test_topology_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: N/A
- manual verification: Context dict keys match template loop expectations

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Active rules loaded and mapped in `lab_page_context()`.
- [ ] Template contract aligned (`label`/`value`/`detail`).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Rich modal HTML via `get_topology_modal_payload` deferred to Low plan optional endpoint.
