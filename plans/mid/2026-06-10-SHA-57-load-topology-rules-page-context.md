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

# Plan: Load and map TopologyRule rows into lab_page_context()

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `topology_rules: []` and `lab_page_context()` never overrides it. `topology_service.get_topology_modal_payload()` exists but has no callers.

## Scope

Add `list_active_topology_rules_for_lab()` and call from `lab_page_context()`. Map ORM fields to template contract (`short_label` → label, `title`/severity → value, `description` → detail).

## Non-goals

- Rich modal JSON endpoint (Low plan).
- `extractor_rules` population.
- Solver validation changes.

## Implementation Plan

1. Read `topology_service.py` and `TopologyRule` model fields.
2. Add `list_active_topology_rules_for_lab()` filtering `is_active=True`, ordered by `sort_order`.
3. Return list of dicts or simple namespace objects with `label`, `value`, `detail` keys.
4. In `lab_page_context()`, after `neutral_lab_context()`, set `context["topology_rules"] = list_active_topology_rules_for_lab()`.
5. Confirm template loop at `asteroid_miner_layout_solver.html` lines ~107–116 works without template change (preferred) or update template to DTO fields if cleaner.
6. Run `python manage.py check`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (only if contract shift needed)

## Validation Plan

- tests: extend `tests/unit/asteroid_lab/test_topology_service.py`
- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py django_apps/web/services/asteroid_lab_page_context.py`

## Acceptance Criteria

- [ ] Active `TopologyRule` rows loaded into page context.
- [ ] Template contract aligned (`label`/`value`/`detail`).
- [ ] Matches the source issue spec.

## Risks / Open Questions

- Inactive rules must be excluded; confirm `is_active` default and queryset filter.
