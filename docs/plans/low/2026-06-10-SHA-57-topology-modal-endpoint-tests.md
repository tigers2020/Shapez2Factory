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

# Plan: Optional topology modal JSON endpoint and integration regression tests

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: Low

## Problem

`get_topology_modal_payload(rule_key)` loads `TopologyRule` joined with `TopologyRuleModalContent` but has zero view/URL callers. No integration test asserts that seeded `TopologyRule` rows appear in Lab page SSR context. Rich per-rule modal content remains unreachable from the UI.

## Scope

- Add integration regression test that seeded active `TopologyRule` rows appear in `lab_page_context()` output.
- Optionally wire `get_topology_modal_payload` to a staff JSON HTTP endpoint for per-rule rich modal content.

## Non-goals

- Core context wiring (covered by High/Mid plans).
- Changing solver topology validation.
- Seeding production topology content.
- Populating `extractor_rules`.

## Implementation Plan

1. Add integration test in `tests/integration/web/` (or extend `tests/unit/asteroid_lab/test_topology_service.py` if no integration harness exists):
   - Seed active `TopologyRule` with known `short_label`, `title`, `description`.
   - Call `lab_page_context(project_id=<id>)` or render Lab view via Django test client.
   - Assert `topology_rules` contains mapped entry with expected `label`/`value`/`detail`.
   - Assert inactive rules are excluded.
2. Evaluate whether rich modal content is needed now:
   - If yes: add staff JSON endpoint (e.g. `GET /internal/staff/topology-rules/<rule_key>/modal/`) calling `get_topology_modal_payload`.
   - Register URL in `config/urls.py` or staff URL module following existing internal staff endpoint patterns.
   - Return 404 when `found=False`, JSON payload when `found=True`.
3. If modal endpoint is deferred, document in issue comment and leave `get_topology_modal_payload` wired only in tests.

## Files / Areas Likely Affected

- `tests/integration/web/` (new or existing test module)
- `tests/unit/asteroid_lab/test_topology_service.py`
- `django_apps/web/views/` (staff endpoint, if implemented)
- `config/urls.py` or staff URL config (if endpoint added)
- `django_apps/asteroid_lab/services/topology_service.py` (existing `get_topology_modal_payload`)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/integration/web/ -k topology -q` or `pytest tests/unit/asteroid_lab/test_topology_service.py -q`
- build: `python manage.py check`
- manual verification: if endpoint added, `curl` staff endpoint returns modal JSON for seeded rule

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Regression test added for Lab page context topology rules.
- [ ] Modal endpoint implemented or explicitly deferred with rationale.

## Risks / Open Questions

- Integration test may need a project fixture and authenticated staff user depending on view access patterns — check existing `tests/integration/web/` conventions.
- Modal endpoint is optional per issue spec; implement only if product needs rich HTML modal content beyond sidebar summary cards.
- Staff endpoint auth pattern must match existing internal staff routes (grep `internal/staff` in `config/` and `django_apps/web/views/`).
