# graph_markup.js research

Date: 2026-05-02

## Targets

- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `django_apps/web/static/web/js/solver_timeline.js`
- `tests/integration/web/test_web_smoke.py`

## Current observations

- One `graph_markup.js` file owns all of:
  - quantity badge formatting
  - shape node preview fallback markup
  - shape card markup
  - operation node markup
  - edge svg path/label markup
  - viewport/stage/zoom control markup
- Public entrypoint is single `renderSolverGraph(graph)`.
- Smoke tests indirectly verify `solver_timeline.js` compatibility marker comment and page render path.
- Hint string currently contains corrupted text `夷?wheel to zoom`.

## Refactoring points

- Splitting preview body, shape header, shape footer badge, controls, hint, stage wrapper shortens node renderer.
- Edge path calculation and edge label markup can also split.
- `renderSolverGraph()` reads better if it only assembles viewport after layout calculation.

## Cautions

- Keep `renderSolverGraph()` export and re-exports `GRAPH_PADDING`, `NODE_HEIGHT`, `NODE_WIDTH`.
- Safer to keep smoke markers `data-graph-viewport`, `preview_image_url`, `No preview`, `./solver_graph_layout.js`.
- When fixing strings, tests still expect `"wheel to zoom"` text included.
