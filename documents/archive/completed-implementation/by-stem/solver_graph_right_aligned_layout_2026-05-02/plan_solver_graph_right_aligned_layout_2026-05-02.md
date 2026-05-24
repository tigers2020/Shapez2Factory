# Plan: solver graph right-aligned layout (2026-05-02)

Related research: [documents/research_solver_graph_right_aligned_layout_2026-05-02.md](./research_solver_graph_right_aligned_layout_2026-05-02.md)

Original request summary: solver graph must have base/source on the left and target/output on the right. Instead of “right-to-left” wording, keep left→right flow but change horizontal graph placement to right-aligned baseline.

## Goals

- Preserve API `graph.layout.direction` as `left-to-right`.
- Keep graph card/edge semantics; change only node horizontal placement to successor-based right-aligned baseline.
- Preserve stable preview behavior and payload.
- Align solver page copy and tests with new meaning.

## Implementation approach

1. Change horizontal placement in `solver_graph_layout.js` to reverse depth order calculation.
2. Sink depth starts at right anchor; remaining nodes at same depth fill leftward.
3. Keep predecessor/successor `COLUMN_GAP` constraints so all edges still flow left→right.
4. Normalize both `x` and `y` to padding baseline in final layout assembly.
5. Replace solver page description with “stable previews + base left / target right + right-aligned layout style”.
6. Update unit/integration tests to new criteria.

## Change targets

- `django_apps/web/static/web/js/solver_graph_layout.js`
- `django_apps/web/templates/web/solver.html`
- `tests/unit/web/test_solver_graph_layout.py`
- `tests/integration/web/test_web_smoke.py`

## Tests

- unit:
  - deterministic layout preserved
  - all edges remain left→right
  - late merge branch can still have different `x` within depth
  - deepest terminal nodes right-aligned on baseline at one-column spacing
- integration:
  - solver page copy reflects change
  - API keeps `graph.layout.direction == "left-to-right"`
- harness:
  - `pytest`
  - `ruff check .`
  - `mypy .`
  - `black .`

## Notes

- Do not change backend DTO/serializer contract in this scope.
- Preview renderer and cache key unrelated; do not touch.
