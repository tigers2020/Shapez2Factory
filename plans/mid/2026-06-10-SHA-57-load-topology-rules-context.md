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

# Plan: Load active TopologyRule rows into lab_page_context

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `"topology_rules": []`. `get_topology_modal_payload()` has zero HTTP callers.

## Scope

Implement `list_active_topology_rules_for_lab()` and wire into `lab_page_context()`. Align template contract (`label`/`value`/`detail`).

## Non-goals

- Extractor rules stub.
- Solver validation changes.

## Implementation Plan

1. In `topology_service.py`, add:

```python
def list_active_topology_rules_for_lab() -> list[dict[str, str]]:
    rules = TopologyRule.objects.filter(is_active=True).order_by("sort_order")
    return [
        {
            "label": rule.short_label,
            "value": rule.title or rule.severity,
            "detail": rule.description,
        }
        for rule in rules
    ]
```

2. In `lab_page_context()`:

```python
context = neutral_lab_context(...)
context["topology_rules"] = list_active_topology_rules_for_lab()
```

3. Confirm template loop at `asteroid_miner_layout_solver.html` lines 107–116 uses matching keys.
4. Add unit test in `test_topology_service.py` for mapping shape.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `tests/unit/asteroid_lab/test_topology_service.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py`

## Acceptance Criteria

- [ ] Active rules loaded ordered by `sort_order`.
- [ ] Template contract aligned.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- `TopologyRuleModalContent` rich HTML may need separate endpoint (Low plan).
