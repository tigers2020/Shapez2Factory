# Plan: materialized graph render parity (2026-05-02)

Related research: [documents/research_materialized_graph_render_parity_2026-05-02.md](./research_materialized_graph_render_parity_2026-05-02.md)

Original request summary: materialized graph appears not to reflect recent card/edge UI changes.

## Goals

- Reduce browser cache collision risk so raw and materialized graphs use the same latest renderer.
- Add test that actual materialized graph payload passes new markup rules.

## Implementation approach

1. Append graph UI version query to `solver_timeline.js` script src on solver page.
2. Append same version query to graph module import chain to separate nested module cache.
3. Add test rendering materialized graph API payload through `renderSolverGraph()`.

## Change targets

- `django_apps/web/templates/web/solver.html`
- `django_apps/web/static/web/js/solver_timeline.js`
- `django_apps/web/static/web/js/solver_timeline/graph_mount.js`
- `django_apps/web/static/web/js/solver_timeline/graph_viewport.js`
- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `tests/unit/web/test_solver_graph_markup.py`

## Verification

- `pytest`
- `ruff check .`
- `mypy .`
- `black .`
