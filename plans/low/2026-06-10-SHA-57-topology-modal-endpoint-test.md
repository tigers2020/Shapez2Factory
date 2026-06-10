---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: Low
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Optional topology modal JSON endpoint and integration regression

## Source Issue

- Linear: SHA-57
- Status at planning time: In Progress
- Priority: Low

## Problem

`get_topology_modal_payload(rule_key)` in `topology_service.py` loads joined `TopologyRule` + `TopologyRuleModalContent` rows but has zero HTTP/view callers. Per-rule rich modal content cannot be fetched client-side if the UI later needs expandable detail beyond the summary cards.

## Scope

Optionally wire `get_topology_modal_payload` to a staff JSON endpoint and add integration regression coverage that Lab SSR includes seeded topology rules end-to-end.

## Non-goals

- Required for SHA-57 acceptance (core fix is context wiring in mid plan).
- Changing modal HTML structure or JS behavior unless product asks.
- Solver topology validation.

## Implementation Plan

1. Assess whether current modal UI reads only SSR `topology_rules` summary cards — if yes, defer endpoint unless product requests rich modal fetch.
2. If endpoint is needed: add thin view in `django_apps/web/views/` calling `get_topology_modal_payload(rule_key)`, map `found=False` to HTTP 404, register URL under existing web URL config.
3. Add integration test asserting Lab page HTTP response contains seeded rule label text:

```python
@pytest.mark.django_db
def test_lab_solver_page_renders_topology_rules(client, lab_project_url):
    m.TopologyRule.objects.create(
        rule_key="visible",
        title="Visible Rule",
        short_label="VR",
        rule_group="g",
        description="Operator help text",
        is_active=True,
    )
    response = client.get(lab_project_url)
    assert response.status_code == 200
    assert b"VR" in response.content
    assert b"Operator help text" in response.content
```

4. If endpoint added, add view test for 404 on missing key and 200 with payload JSON on hit.
5. Run: `pytest tests/integration/web/test_lab_topology_rules_context.py -v`

## Files / Areas Likely Affected

- `django_apps/web/views/` (optional new endpoint)
- `django_apps/web/urls.py` or sibling URL module (optional)
- `tests/integration/web/test_lab_topology_rules_context.py`
- `django_apps/asteroid_lab/services/topology_service.py` (existing `get_topology_modal_payload` — no change expected)

## Validation Plan

- lint: `ruff check django_apps/web/views/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/ -k topology -v`
- build: `python manage.py check`
- manual verification: optional fetch of modal JSON endpoint if implemented

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Endpoint may be YAGNI if modal only uses SSR summary cards — confirm with product before building.
- Staff-only auth on modal endpoint if exposed publicly.
