---
linear_issue: SHA-57
title: Lab page context hardcodes topology_rules []; TopologyRule catalog never reaches UI
priority: High
labels:
  - bug
  - ui
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Surface curated topology guidance in Lab UI

## Source Issue

- Linear: SHA-57
- Status at planning time: Todo
- Priority: High

## Problem

`lab_page_context()` always supplies `topology_rules: []` despite active `TopologyRule` rows in the database. The Lab topology panel permanently shows empty-state copy even when staff-curated rules exist.

## Scope

Ensure operators see active topology guidance in the Lab solver page topology panel/modal by loading and exposing curated rules in page context.

## Non-goals

- Do not populate `extractor_rules` (separate stub).
- Do not change solver topology validation behavior.
- Do not seed production topology content (ops/data task).

## Implementation Plan

1. Confirm template contract in `asteroid_miner_layout_solver.html` expects `label`, `value`, `detail` per rule.
2. Load active `TopologyRule` rows (`is_active=True`, ordered by `sort_order`) in `lab_page_context()`.
3. Map ORM fields to template shape (`short_label` → label, `title`/severity → value, `description` → detail).
4. Verify Lab SSR renders rule list instead of permanent empty-state when rules are seeded.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/asteroid_lab/services/topology_service.py`
- `django_apps/web/templates/web/asteroid_miner_layout_solver.html`

## Validation Plan

- lint: `ruff check django_apps/web/services/asteroid_lab_page_context.py django_apps/asteroid_lab/services/topology_service.py`
- typecheck: `mypy django_apps config src`
- tests: regression in Low plan
- build: n/a
- manual verification: seeded rules visible in Lab topology panel

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Seeded active topology rules appear in Lab page context.
- [ ] Template renders rule list instead of permanent empty-state.
- [ ] Solver validation behavior unchanged.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Rich modal HTML may require a separate endpoint (optional Low plan item).
