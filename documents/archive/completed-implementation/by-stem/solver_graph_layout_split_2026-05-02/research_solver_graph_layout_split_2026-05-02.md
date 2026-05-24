# solver_graph_layout.js research

Date: 2026-05-02

## Targets

- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `tests/integration/web/test_web_smoke.py`

## Current observations

- `solver_graph_layout.js` is graph runtime layout core but algorithm steps run long in one file.
- Especially `computeGroupedGraphLayout()` assembles all steps directly:
  - depth calculation
  - column grouping
  - barycenter ordering
  - adjacency preparation
  - top position iterative adjustment
  - horizontal position calculation
  - final x/y position generation
  - bounds calculation
- External public contract is effectively `computeGraphLayout()` and constant exports.

## Refactoring points

- Splitting empty graph layout, ordered column preparation, vertical pass iteration, final position/bounds calculation shortens main function greatly.
- Bundling adjacency and sorted depths once before repeated calculation reads better.
- Vertical placement forward/backward sweep pair suits two helpers or one pass runner.

## Cautions

- Smoke tests do not assert layout numbers directly but broken graph render causes indirect page regression.
- Keep `transform-origin: 0 0;`, viewport size styles, `./solver_graph_layout.js` marker.
- Goal is structural split, not algorithm semantic change.
