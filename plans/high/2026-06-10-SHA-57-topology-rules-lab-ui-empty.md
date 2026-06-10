---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: High
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Restore curated topology guidance in Lab UI

## Source Issue

- Linear: SHA-57
- Status at planning time: In Progress
- Priority: High

## Problem

The Asteroid Lab solver page renders a Topology Constraints modal and sidebar panel from `topology_rules`, but `lab_page_context()` always supplies an empty list via `neutral_lab_context()`. Staff-curated `TopologyRule` rows exist in the database but never reach the template, so operators permanently see the empty-state copy (“Run Solver to generate constraints”) even when active rules are seeded.

## Scope

Ensure active `TopologyRule` catalog rows are loaded and exposed through `lab_page_context()` so the Lab topology panel and modal render operator help instead of the permanent empty state.

## Non-goals

- Populating `extractor_rules` (separate stub).
- Changing solver topology validation behavior.
- Seeding production topology content (ops/data task).

## Implementation Plan

1. Add `list_active_topology_rules_for_lab()` in `django_apps/asteroid_lab/services/topology_service.py` that queries `TopologyRule.objects.filter(is_active=True).order_by("sort_order", "rule_key")`.
2. Map each ORM row to a template-ready dict: `label` ← `short_label`, `value` ← `title` (or `severity` if title is empty), `detail` ← `description`.
3. In `lab_page_context()` (`django_apps/web/services/asteroid_lab_page_context.py`), after `neutral_lab_context()`, set `ctx["topology_rules"]` from the new helper (including when `project_id is None` so neutral shell still shows catalog).
4. Verify template `{% for rule in topology_rules %}` in `asteroid_miner_layout_solver.html` renders rows and opens the sidebar `<details>` panel when rules exist (`{% if topology_rules %}open{% endif %}`).
5. Manually seed one active `TopologyRule` in dev DB and confirm Lab page shows rule cards instead of empty-state paragraph.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (verify only; no change expected if mapping matches contract)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/topology_service.py django_apps/web/services/asteroid_lab_page_context.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: covered in mid-priority plan
- build: `python manage.py check`
- manual verification: load Lab solver page with seeded active `TopologyRule`; confirm modal and sidebar show rule list

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Sidebar summary text (“Run Solver to generate constraints”) is hardcoded and does not reflect catalog presence; may need a follow-up copy tweak outside this scope.
- `value` field mapping (`title` vs `severity`) should match operator expectations; confirm with existing admin seed data.
