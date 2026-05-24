# Plan: solver graph card cleanup and straight edge routing (2026-05-02)

Related research: [documents/research_solver_graph_card_cleanup_2026-05-02.md](./research_solver_graph_card_cleanup_2026-05-02.md)

Original request summary: remove preview card internal scroll in solver graph, separate multi-input lines for readability, change curved edges to elbow straight segments.

## Goals

- Shape preview cards look like fixed cards without internal scrollbars.
- Operation card multi-inputs like `Input A/B` use distinct arrival lanes.
- Edge paths render as elbow polylines with `M/L` instead of cubic bezier.
- Do not change solver graph payload or backend graph generation.

## Implementation approach

1. In `graph_markup.js`, reduce shape card root overflow and internal spacing; fix preview height.
2. Split edge geometry helper to compute source/destination anchors and lane offsets.
3. Apply slot-label-based lane index for operation input/output.
4. Move edge labels near destination-side horizontal segment.
5. Add graph markup unit tests and strengthen smoke test markers.

## Change targets

- `django_apps/web/static/web/js/solver_timeline/graph_markup.js`
- `tests/unit/web/test_solver_graph_markup.py`
- `tests/integration/web/test_web_smoke.py`

## Verification

- `pytest`
- `ruff check .`
- `mypy .`
- `black .`

## Notes

- Keep `solver_graph_layout.js` node height for now; review whether card compression alone suffices.
- Can extend shape/output fanout lane separation in follow-up if needed.
