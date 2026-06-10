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

# Plan: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: High

## Problem

The Asteroid Lab solver page renders a Topology Constraints modal and sidebar panel from `topology_rules`, but `lab_page_context()` always supplies an empty list. Staff-curated `TopologyRule` rows exist in the database, yet the UI permanently shows the empty-state copy ("Run Solver to generate constraints") even when active rules are present.

## Scope

- Restore operator visibility of curated topology guidance in the Lab UI by ensuring active `TopologyRule` catalog rows reach the SSR page context and render in the topology panel/modal.
- Fix the broken user-facing behavior: empty-state shown despite DB content.

## Non-goals

- Populating `extractor_rules` (separate stub).
- Changing solver topology validation behavior.
- Seeding production topology content (ops/data task).
- Rich per-rule modal JSON endpoint (deferred to Low priority plan).

## Implementation Plan

1. Confirm the template contract in `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (lines 107–116): each rule needs `.label`, `.value`, `.detail`.
2. Add `list_active_topology_rules_for_lab()` in `django_apps/asteroid_lab/services/topology_service.py` that queries `TopologyRule.objects.filter(is_active=True).order_by("sort_order", "rule_key")`.
3. Map ORM fields to template-ready dicts: `short_label` → `label`, `title` (or `severity`) → `value`, `description` → `detail`. Include `rule_key` for future modal wiring.
4. In `lab_page_context()` (`django_apps/web/services/asteroid_lab_page_context.py`), override `ctx["topology_rules"]` after `neutral_lab_context()` — for both project and no-project paths so the catalog is always visible.
5. Manually verify: seed one active `TopologyRule`, load Lab solver page, confirm topology panel lists the rule instead of empty-state copy.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html` (read-only unless contract changes)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_topology_service.py -q` plus new context regression test
- build: `python manage.py check`
- manual verification: Lab solver page topology panel shows seeded rules; empty-state copy absent when rules exist

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Seeded active topology rules appear in Lab page context.
- [ ] Template renders rule list instead of permanent empty-state.

## Risks / Open Questions

- Template uses attribute access (`.label`/`.value`/`.detail`); dicts work in Django templates but a small `NamedTuple` or dataclass may be clearer.
- `lab_page_context()` returns early when `project_id is None`; topology catalog should still load on that path.
- Depends on Mid plan for full mapping contract alignment and regression tests.
