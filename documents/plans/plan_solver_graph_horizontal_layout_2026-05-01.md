# Plan: Solver Graph Horizontal Layout

## Summary

Relax the solver graph's fixed depth-column `x` placement while keeping deterministic left-to-right DAG edges. The goal is to let late-joining parallel branches spread horizontally before they merge, so related work stays readable without forcing every same-depth node onto the same vertical band.

## Changes

- Keep the existing frontend-only contract in `django_apps/web/static/web/js/solver_graph_layout.js`.
- Preserve `computeNodeDepths`, barycenter ordering, and vertical compaction for stable branch grouping.
- Add per-node horizontal placement based on edge monotonicity: every edge target remains to the right of its source by at least the configured gap.
- Add same-rank spacing so nodes with the same topological depth can occupy different `x` positions when that improves readability.
- Recompute `layout.width`, `layout.height`, and `bounds` from actual node boxes.
- Leave solver API DTOs, serializers, and `solver_timeline.js` rendering contract unchanged unless a small edge-curve guard is needed.

## Verification

- Extend `tests/unit/web/test_solver_graph_layout.py` with edge monotonicity checks.
- Add a late-merge parallel-chain graph that proves same-rank branch nodes are no longer locked to identical `x` positions.
- Keep deterministic output and bounds coverage tests green.
- Run the harness sequence: `pytest`, `ruff check .`, `mypy .`, and `black .`.

## Tradeoffs

- The graph can become wider because same-rank nodes may spread horizontally.
- The layout remains deterministic and DAG-oriented; it does not become a force-directed freeform layout.
