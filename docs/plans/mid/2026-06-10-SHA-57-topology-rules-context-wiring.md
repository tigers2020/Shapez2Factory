---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Topology rules context wiring and template contract alignment

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `"topology_rules": []` and `lab_page_context()` never overrides it. No Python code maps `TopologyRule` ORM fields into the template contract (`label`/`value`/`detail`). The existing `TopologyRuleSummaryDTO` and `get_topology_modal_payload()` service are unused by the Lab SSR path.

## Scope

- Implement `list_active_topology_rules_for_lab()` helper with explicit field mapping from `TopologyRule` to template contract.
- Wire the helper into `lab_page_context()` so active rules populate context on every Lab page render.
- Align template contract: either map to `label`/`value`/`detail` dicts or update template to use DTO field names (prefer mapping to avoid template churn).

## Non-goals

- HTTP endpoint for per-rule modal payloads (Low priority).
- `extractor_rules` population.
- Solver topology validation changes.
- Production data seeding.

## Implementation Plan

1. Define return type for `list_active_topology_rules_for_lab()` — list of dicts with keys `label`, `value`, `detail`, `rule_key` (mapping: `short_label` → `label`, `title` → `value`, `description` → `detail`).
2. Implement query in `topology_service.py`:
   ```python
   TopologyRule.objects.filter(is_active=True).order_by("sort_order", "rule_key")
   ```
3. Add unit test in `tests/unit/asteroid_lab/test_topology_service.py`:
   - Seed two rules (one inactive), assert only active rules returned in sort order with correct field mapping.
4. In `lab_page_context()`, after `ctx = neutral_lab_context()`, set:
   ```python
   ctx["topology_rules"] = list_active_topology_rules_for_lab()
   ```
   Apply before the `if project_id is None: return ctx` early exit so rules appear even without a project.
5. Verify template `{% for rule in topology_rules %}` renders mapped fields without template edits.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/asteroid_lab/services/dto.py` (read `TopologyRuleSummaryDTO` for field reference)
- `django_apps/web/services/asteroid_lab_page_context.py`
- `tests/unit/asteroid_lab/test_topology_service.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -q`
- build: `python manage.py check`
- manual verification: topology sidebar panel lists rules with correct label/value/detail text

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Active `TopologyRule` rows loaded and mapped in `lab_page_context()`.
- [ ] Template contract alignment (`label`/`value`/`detail`) verified.

## Risks / Open Questions

- Whether `severity` should be used instead of `title` for the `value` column — issue spec says "title or severity"; default to `title`, document if severity is preferred.
- Inactive rules must be excluded; confirm `is_active=False` rows never appear.
- High-priority plan covers end-to-end operator visibility; this plan covers implementation detail.
