---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
  - test
  - question
status: planned
created_by: todo-plan-automation
---

# Plan: Staff template, bootstrap JSON, and recompute route

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Mid

## Problem

No Django template mounts the editor; no recompute route exists; bootstrap JSON fields are never set in production templates.

## Scope

Restore staff template, bootstrap JSON, and POST recompute route; document human decision on post-0009 `graph_document` persistence target.

## Non-goals

- Removing or rewriting React editor source.
- Double `validate_graph_document` if using `recompute_validated_graph_document`.

## Implementation Plan

1. Review documented API flow in `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` section 3.2.
2. Create staff template per DESIGN.md mount contract with catalog/recipe JSON scripts and static bundle includes.
3. Implement `macro_pattern_staff_api_recipe_graph_recompute` view calling `recompute_graph_document`, `domain_graph_to_react_flow`, validation enrichment.
4. Register route in `urls.py` with staff auth gate.
5. Document persistence decision: draft-only API vs new storage model vs game_data snapshot.
6. Avoid double validation when input is pre-validated.

## Files / Areas Likely Affected

- `django_apps/web/templates/` (new template)
- `django_apps/web/views/staff_shared.py`
- `django_apps/web/urls.py`
- `documents/notes/recipe_graph_bottleneck_report_2026-05-04.md` (reference)

## Validation Plan

- lint: `ruff check django_apps/web/views/staff_shared.py`
- typecheck: `mypy django_apps config src`
- build: `python manage.py check`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Persistence contract is a human decision blocker; implement draft-only mode if decision is deferred.
