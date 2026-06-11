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

# Plan: Load and map active TopologyRule rows into lab_page_context

## Source Issue

- Linear: SHA-57
- Status at planning time: In Progress
- Priority: Mid

## Problem

`neutral_lab_context()` hardcodes `"topology_rules": []` and `lab_page_context()` never overrides it. The template expects objects with `.label`, `.value`, `.detail` attributes but no Python code maps `TopologyRule` ORM fields into that shape.

## Scope

Implement the service helper and context wiring with template contract alignment (`label`/`value`/`detail`), plus unit test coverage for the list helper and context key population.

## Non-goals

- Optional per-rule rich modal JSON endpoint (low-priority plan).
- Template redesign beyond attribute contract alignment.
- Solver validation changes.

## Implementation Plan

1. **Write failing unit test** in `tests/unit/asteroid_lab/test_topology_service.py`:

```python
@pytest.mark.django_db
def test_list_active_topology_rules_for_lab_maps_template_contract() -> None:
    m.TopologyRule.objects.create(
        rule_key="rim-only",
        title="Rim placement only",
        short_label="Rim",
        rule_group="placement",
        severity="warn",
        description="Extractors must sit on rim cells.",
        is_active=True,
        sort_order=1,
    )
    m.TopologyRule.objects.create(
        rule_key="inactive",
        title="Hidden",
        short_label="X",
        rule_group="g",
        is_active=False,
    )
    rows = topology_service.list_active_topology_rules_for_lab()
    assert len(rows) == 1
    assert rows[0]["label"] == "Rim"
    assert rows[0]["value"] == "Rim placement only"
    assert rows[0]["detail"] == "Extractors must sit on rim cells."
```

2. Run: `pytest tests/unit/asteroid_lab/test_topology_service.py::test_list_active_topology_rules_for_lab_maps_template_contract -v` — expect FAIL.

3. Implement `list_active_topology_rules_for_lab()` returning `list[dict[str, str]]` with keys `label`, `value`, `detail`.

4. Import and call from `lab_page_context()`:

```python
from django_apps.asteroid_lab.services import topology_service

# inside lab_page_context, after ctx = neutral_lab_context():
ctx["topology_rules"] = topology_service.list_active_topology_rules_for_lab()
```

5. **Write failing integration test** (new file `tests/integration/web/test_lab_topology_rules_context.py` or extend existing web context tests if present):

```python
@pytest.mark.django_db
def test_lab_page_context_includes_active_topology_rules(client, project_fixture):
    m.TopologyRule.objects.create(
        rule_key="test-rule",
        title="Test",
        short_label="T",
        rule_group="g",
        description="desc",
        is_active=True,
    )
    ctx = lab_page_context(project_id=project_fixture.id, project_slug=project_fixture.slug)
    assert len(ctx["topology_rules"]) == 1
    assert ctx["topology_rules"][0]["label"] == "T"
```

6. Run focused tests: `pytest tests/unit/asteroid_lab/test_topology_service.py tests/integration/web/test_lab_topology_rules_context.py -v`

7. Run `python manage.py check`

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `tests/unit/asteroid_lab/test_topology_service.py`
- `tests/integration/web/test_lab_topology_rules_context.py` (new, if no existing web context test file)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py django_apps/web/services/asteroid_lab_page_context.py tests/unit/asteroid_lab/test_topology_service.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -v` plus integration test above
- build: `python manage.py check`
- manual verification: TBD (covered in high-priority plan)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Whether to use `types.SimpleNamespace` vs plain dicts for template dot-access — dicts work in Django templates via key lookup; existing tests should confirm.
- Integration test may need existing project fixture pattern from sibling web tests; follow local convention.
