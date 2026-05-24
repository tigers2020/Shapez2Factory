# Solver Search Strategy: Shortest Path by Operation Cost

## Why Simple Recursive Decomposition May Be Insufficient

Multiple production paths can reach the same target shape.

Example: `RcCuRcCu` might be built roughly by:

- Quad cut + repeated stacking
- Two wide solid shapes → rotate/align then **swap halves**
- Build halves then stack

So a "single fixed decomposition rule" cannot guarantee minimum buildings/steps.

## Algorithm Candidates

| Method | When Useful |
| --- | --- |
| **BFS** | Uniform operation cost and small state space |
| **Dijkstra** | **Weighted costs** differ (operations, buildings, throughput penalties) |
| **A*** | Heuristic from **quadrant mismatch** between target and current shape |

## Codebase Location (Reference)

Some search/matching logic already lives in `shapez_solver` unit tests and services (e.g. inventory/prebuilt pattern search). Building a general **minimum-cost graph search to target shape** is a separate plan.

## Notes

- State can be normalized `Shape` plus optional **paint resource vector** ([operation_color_mixer.md](operation_color_mixer.md)).
- Review heuristic **admissibility** (under-estimation can break A* optimality).
