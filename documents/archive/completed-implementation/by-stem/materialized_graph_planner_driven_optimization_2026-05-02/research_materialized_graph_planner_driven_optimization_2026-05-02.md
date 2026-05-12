# Materialized Graph Planner-Driven Optimization Research

## Context

- Target area: `django_apps/shapez_solver/services/materialized_graph_builder.py`
- Goal: remove waste from the single-layer materialized fast-path that ignores the planner's chosen recipe.

## Current Behavior

- `MaterializedGraphBuilder.build()` returns `None` when `base_demands` are unavailable.
- When `base_demands` exist and the target is a supported single-layer shape, the builder bypasses the solved recipe and enters `_build_single_layer_batch_graph()`.
- That path reconstructs output targets from raw full sources by forcing this sequence:
  - full source cut into halves
  - rotate halves
  - cut halves into quadrants
  - align quadrants
  - re-stack quadrants
  - optionally paint the final target

## Mismatch With Planner

- The planner already chooses a cheaper deterministic recipe in `PlannerService`.
- Rule priority in `django_apps/shapez_solver/services/planner_service.py` prefers `try_assemble_halves()` before `try_assemble_quadrants()`.
- The materialized fast-path discards that result and rebuilds a separate quarter-based assembly graph anyway.

## Observed Waste Cases

### `RuRu----`

- Planner recipe: `cutter`
- Materialized fast-path: generates repeated `cutter`, `rotate_ccw`, `rotate_180`, and `stacker` operations for the same batch target count.
- Waste: half output already matches the useful build unit, so quarter decomposition and reassembly add no value.

### `CuRu----`

- Planner recipe: quarter derivation plus `stacker`
- Materialized fast-path: still starts from forced quarter pool generation for every source, then performs additional alignment and stacking unrelated to the solved recipe structure.
- Waste: the builder duplicates planning decisions instead of materializing the chosen graph.

### `CuRuSuSu`

- Planner recipe includes `swapper` after upstream derivation.
- Materialized fast-path omits planner intent and reconstructs everything through quarter pooling and repeated `stacker` chains.
- Waste: operation count and node count grow significantly beyond the solved recipe demand.

## Implementation Direction

- Keep `source-only` materialization as the simple special case.
- For every other supported batch materialization case, consume `SolvedRecipe.recipes` plus `_compute_output_demands()` as the single source of truth.
- Preserve `base_demands.full_source_count` as the source clone quantity contract.
- Remove materialized-only quadrant pool logic so quarter assembly appears only when the planner explicitly chose quarter assembly.
