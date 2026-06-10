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

# Plan: Load active TopologyRule rows into lab_page_context

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `topology_rules: []` and `lab_page_context()` never overrides it.

## Scope

Add `list_active_topology_rules_for_lab()` helper and call it from `lab_page_context()` with template contract alignment.

## Non-goals

- Do not wire `extractor_rules`.
- Do not change solver validation.

## Implementation Plan

1. Add `list_active_topology_rules_for_lab()` beside `topology_service.py` returning template-ready dicts.
2. Call from `lab_page_context()` after `neutral_lab_context()` to set `topology_rules`.
3. Align field mapping with template `{% for rule in topology_rules %}` expecting `.label`, `.value`, `.detail`.
4. Extend `tests/unit/asteroid_lab/test_topology_service.py` for list helper behavior.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `tests/unit/asteroid_lab/test_topology_service.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py django_apps/web/services/asteroid_lab_page_context.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Active rules loaded and mapped into context.
- [ ] Template contract aligned.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- `get_topology_modal_payload(rule_key)` has zero HTTP callers; rich modal may need separate endpoint (Low plan).
