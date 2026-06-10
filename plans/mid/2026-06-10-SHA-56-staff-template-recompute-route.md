---
linear_issue: SHA-56
title: Recipe graph editor Django wiring missing: no staff page, no recompute API, bootstrap URL never set
priority: Mid
labels:
  - bug
  - ui
  - test
  - question
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Restore staff template, bootstrap JSON, and POST recompute route

## Source Issue

- Linear: SHA-56
- Status at planning time: Todo
- Priority: Mid

## Problem

`useRecipeGraphRecompute` reads empty `bootstrap.api_recipe_graph_recompute`; no Django template provides `#macro-graph-bootstrap`; no recompute URL in `urls.py`.

## Scope

Reintroduce staff template per DESIGN.md mount contract; add POST recompute route; populate bootstrap JSON with API URLs and initial React Flow document.

## Non-goals

- SHA-23/SHA-24 validation fixes.
- CI bundle build (SHA-40).

## Implementation Plan

1. Create staff template (e.g. `web/templates/web/staff_recipe_graph_editor.html`) with:
   - `#macro-graph-editor-root`
   - `#macro-graph-bootstrap` JSON script
   - Static includes for `recipe-graph-editor.js` and catalog scripts
2. Add view rendering template with bootstrap dict:

```python
bootstrap = {
    "api_recipe_graph_recompute": reverse("macro_pattern_staff_api_recipe_graph_recompute"),
    "api_shape_part_sprite_manifest": reverse(...),  # if used
    "react_flow_initial": initial_document,
}
```

3. Implement `macro_pattern_staff_api_recipe_graph_recompute` POST handler:
   - Staff auth gate (`@staff_member_required` or existing staff decorator)
   - Parse `graph_document` from body
   - Call `recompute_validated_graph_document` or `recompute_graph_document` + adapter
   - Return JSON: `react_flow`, `validation`, optional `commit` persistence
4. Register route in `django_apps/web/urls.py`.
5. Avoid double `validate_graph_document` if using pre-validated recompute helper.

## Files / Areas Likely Affected

- `django_apps/web/templates/web/` (new staff page)
- `django_apps/web/views/staff_shared.py`
- `django_apps/web/urls.py`
- `django_apps/shapez_solver/services/recipe_graph_recompute.py`
- `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py`

## Validation Plan

- tests: integration tests from Low plan
- django check: `python manage.py check`

## Acceptance Criteria

- [ ] Bootstrap includes `api_recipe_graph_recompute`.
- [ ] Staff-only POST route registered and callable.
- [ ] Human decision on post-0009 persistence documented.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.

## Risks / Open Questions

- Persistence target blocks `commit=true` implementation; draft-only may be acceptable interim.
