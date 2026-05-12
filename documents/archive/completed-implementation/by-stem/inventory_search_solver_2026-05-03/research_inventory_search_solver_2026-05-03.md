# Research: inventory search solver pipeline (2026-05-03)

## Scope

Batch-aware **inventory state search** (uniform-cost / Dijkstra) to replace single-target recursive recipe planning for the MVP operations: rotate, cut, swap, stack, full sources, batch counts from `compute_factory_batch`.

## Code references

- Demand / batch: [`django_apps/shapez_solver/domain/factory_demand.py`](../django_apps/shapez_solver/domain/factory_demand.py) — `FactoryBatch.base_source_counts`, `target_count`.
- Legacy pipeline: [`django_apps/shapez_solver/services/solve_pipeline.py`](../django_apps/shapez_solver/services/solve_pipeline.py) — planner → recipe graph; batch only decorates graph.
- New solver: [`django_apps/shapez_solver/services/inventory_search_solver.py`](../django_apps/shapez_solver/services/inventory_search_solver.py), [`action_generator.py`](../django_apps/shapez_solver/services/action_generator.py), [`operation_semantics.py`](../django_apps/shapez_solver/services/operation_semantics.py).
- Swapper contract: [`django_apps/shapez_solver/services/operation_engine.py`](../django_apps/shapez_solver/services/operation_engine.py) — `swapper` requires both operands **single-layer** (`len(layers)==1`). **Stacker** on two single-layer full shapes yields a **two-layer** canonical code (`base:top`), so naive pair generation must not call swapper on multi-layer codes.

## Findings

1. `compute_factory_batch` already encodes balanced `target_count` and per-base `full_source_count`; this map is the correct initial inventory for search.
2. Graph DTO today: [`SolverGraphEdge`](../django_apps/shapez_solver/dto/solver_graph.py) had no quantity field; flow fidelity needs optional edge quantity (default 1) for adapters.
3. Feature selection: solver mode should be configurable (Django settings + optional request override) with legacy fallback on `InventorySearchError` or validation failure.
4. **Search goal vs paint**: primitive inventory search does not run painters. The search goal code must match uncolored full-source outputs; use `inventory_search_goal_shape_code(target)` (see `factory_demand.py`) so targets like `RcCuRcCu` line up with `RuRuRuRu`/`CuCuCuCu` batch sources.

## Non-goals (this increment)

Painter/color mixer, pins/crystals, train/belt throughput, full UI redesign (see parent rebuild plan).
