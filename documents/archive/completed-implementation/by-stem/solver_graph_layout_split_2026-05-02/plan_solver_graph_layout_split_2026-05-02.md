# solver_graph_layout.js refactoring plan

Date: 2026-05-02

## Goals

- Split layout calculation steps in `solver_graph_layout.js` into helpers to simplify main flow.
- Preserve output coordinates and bounds contract.

## Change scope

- `django_apps/web/static/web/js/solver_graph_layout.js`

## Approach

1. Extract empty graph fallback helper.
2. Add layout state helper bundling ordered column, adjacency, sorted depth.
3. Separate vertical top position sweep helper.
4. Separate final positions and bounds calculation helpers.
5. Verify graph page regression via smoke tests.

## Expected benefits

- Main layout function reads as “prepare → vertical placement → horizontal placement → bounds”.
- Smaller edit surface when tuning layout algorithm later.
