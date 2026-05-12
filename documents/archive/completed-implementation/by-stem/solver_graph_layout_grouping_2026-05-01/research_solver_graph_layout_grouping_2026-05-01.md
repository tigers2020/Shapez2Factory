# Solver Graph Layout Grouping Research

- Date: 2026-05-01
- Scope: `django_apps/web/static/web/js/solver_graph_layout.js`

## Findings

- The current graph layout is computed entirely on the frontend in `computeGraphLayout()`.
- The reusable layout code now lives in `django_apps/web/static/web/js/solver_graph_layout.js`; `solver_timeline.js` consumes the returned positions, bounds, width, and height.
- Nodes are still assigned an `x` position by graph depth, even after `y` positions are grouped by barycenter ordering and vertical compaction.
- This creates a top-aligned stacked-column layout even when two nodes belong to different branches and should appear closer to their related neighbors.
- For late-joining branches such as a CuRuSuSu-style chain, fixed depth columns also keep parallel work aligned from the first layer, which can stretch edge curves long before the branches need to merge.
- The solver API already returns enough graph structure (`nodes`, `edges`, `layout.direction`) to compute grouped layout client-side without changing backend DTOs or serializers.
- The existing viewport code only depends on `layout.width`, `layout.height`, and `bounds`, so a new layout algorithm can be introduced if those values remain accurate.
- There is no existing JS unit test harness, but `node` is available locally and the file is already an ES module, so Python tests can exercise exported layout helpers through `node --input-type=module`.

## Implementation Direction

- Keep the left-to-right DAG constraint by preserving edge monotonicity instead of fixed depth columns.
- Replace the per-column index stacking with barycenter ordering across multiple passes.
- Compact vertical spacing after ordering so related branches stay visually closer together.
- Assign per-node `x` positions from predecessor constraints and same-rank spacing so late-joining branches can spread horizontally before they merge.
- Recompute graph `width` and `bounds` from actual positions rather than from max depth.
- Preserve deterministic output by using stable tie-breaking from original node order.
