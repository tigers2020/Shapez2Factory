# solver graph right-aligned layout research

Date: 2026-05-02

## Request summary

Preserve solver graph data flow as `base/source -> target/output` left→right. Realign horizontal placement from left-anchored expansion to right anchor so target side has more consistent right baseline.

## Current structure summary

- Graph direction metadata: `SolverGraph.direction` in `django_apps/shapez_solver/dto/solver_graph.py`, currently `left-to-right`.
- API serialization passes through as `graph.layout.direction` in `django_apps/shapez_solver/view_graph_serialization.py`.
- All coordinate math is frontend-only in `django_apps/web/static/web/js/solver_graph_layout.js`.
- Graph cards and edge SVG consumed by `django_apps/web/static/web/js/solver_timeline/graph_markup.js`.
- Solver page guidance rendered directly in `django_apps/web/templates/web/solver.html`.

## Current layout behavior observations

`computeHorizontalPositions()` proceeds left to right by depth order:

1. Pushes next node right based on minimum `x` already taken by predecessor
2. Places next node at same depth further right using `nextRankLeft`

This preserves left→right edge monotonicity but short side branches stop earlier on the left by branch length, weakening target-side right alignment.

Example:

- In current sample graph, deepest targets `shape:target` and `shape:side-target` share depth but `x` gap is two columns (`540px`) not one.
- Sink-depth nodes follow left-anchored upstream placement rather than right baseline alignment.

## Change direction

- Keep graph meaning and API direction metadata as `left-to-right`.
- Process horizontal coordinates in reverse depth order: satisfy successor constraints first, pack nodes as far right as possible.
- Within same depth, fill right to left while preserving order, forming right-aligned baseline.
- In final `buildFinalGraphLayout()`, normalize `x` like `y` to move whole graph inside padding.

## Impact scope

- Change required:
  - `django_apps/web/static/web/js/solver_graph_layout.js`
  - `django_apps/web/templates/web/solver.html`
  - `tests/unit/web/test_solver_graph_layout.py`
  - `tests/integration/web/test_web_smoke.py`
- No change:
  - `SolverGraph.direction`
  - graph serializer payload shape
  - graph preview renderer / cache / fallback
  - edge meaning (`from -> to`)

## Testing perspective

- Keep existing left-to-right edge verification.
- New check: terminal nodes at same depth align on target-side right baseline at one-column spacing.
- Smoke test should describe left→right flow and right-aligned layout style, not `right-to-left DAG`.

## Conclusion

Backend contract unchanged; this is primarily frontend layout algorithm swap. Core implementation: change horizontal placement in `solver_graph_layout.js` from predecessor-forward to successor-based reverse right-anchor placement.
