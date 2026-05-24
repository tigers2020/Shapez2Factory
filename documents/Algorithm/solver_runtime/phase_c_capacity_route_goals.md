---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: C
pr: 2.5
related_docs:
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase C ? Capacity Planner / RouteGoal Planner

## Purpose

Determine required external `RouteGoal` count based on map size and expected candidate count. **Does not install actual belt/pipe.**

## Input

```text
OptimizationInput
solver config (optional)
```

## Output

```text
PlannedRouteGoals
capacity_plan
```

**`OptimizationInput.route_goals` canonical:** Phase C generates·augments planned goal set used by probe·commit·validation. Phase B uses empty/seed only ([`phase_b_optimization_input.md`](phase_b_optimization_input.md)).

## Tasks

### Throughput canonical

Shape:

```text
12 fully boosted miners = 1 saturated Space Belt
```

Fluid:

```text
72 fully boosted pumps = 1 saturated Space Pipe
```

CANON: [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

### Estimation (geometry heuristic)

`mineable / 5` alone is not a game rule; it separates pattern max footprint (extractor+extension+output stub ? 5 cells) from runtime layout variance.

```python
PLATFORM_FOOTPRINT_CELLS = 5
DEFAULT_MINEABLE_PACKING_EFFICIENCY = 0.75  # v0; tunable via solver config in v1)

estimated_extractor_groups = floor(
    mineable_cell_count * packing_efficiency / PLATFORM_FOOTPRINT_CELLS
)
```

OD-2: [`open_decisions.md`](open_decisions.md).

### Goal count (throughput CANON)

```python
shape_goal_count = ceil(estimated_extractor_groups / 12)
fluid_goal_count = ceil(fluid_platform_count / 72)
```

`12` / `72` are Space Belt / Space Pipe saturation ratios ([`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md), capacity·trunk aligned).

### RouteGoal generation

Generate goals from external margin / external void / existing trunk attachment info.

```python
RouteGoal(
    coord=coord,
    goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
    transport_kind=TransportKind.SHAPE_BELT,
    priority=20,
    existing_trunk=False,
)
```

### Goal count cap (shape)

```python
throughput = ceil(estimated_extractor_groups / 12)
extractor_scaled = estimated_extractor_groups * 2
shape_goal_count = min(8, max(2, min(throughput, extractor_scaled)))
```

From 2 extractors onward, `groups*2` is preferred over throughput(1) so goals do not become excessive.

### Goal selection policy (v0)

Prerequisite: Phase B provides `route_domain_bbox = asteroid_bbox + OUTER_VOID_PADDING(10)` and padded `external_void_cells`.

1. In `external_void_cells`, **mineable BFS distance `3 <= d <= 5`** (BFS within `route_domain_bbox`)
2. **Top/bottom bilateral split** ? side band·even spacing based on **`mineable_cells` / `asteroid_bbox` extent** (`width >= height` ? **top/bottom wide face** `y` band, even spread along `x`; else **left/right wide face** `x` band, spread along `y`; `side_band_width = max(2, wide_face_span//8)`)
3. `first_count = total // 2`, `second_count = total - first_count` ? from each wide face, **even target** at `span / (count + 1)` based on rim ? snap to nearest void (outer tie-break)
4. **shape goals** placed bilaterally first; **fluid** in separate bilateral pass (`used` shared ? coordinate overlap forbidden)
5. **Tie-break:** same face·cardinal sector·outer corner filter

`PlannedRouteGoals` records `spread_axis` (`x`=horizontal even spacing on top/bottom rim, `y`=vertical), `shape_goals_shortfall` / `fluid_goals_shortfall`.

**Replay:** After `ROUTE_GOAL_GENERATED`, all timeline frames accumulate `route_goal` overlay in `map_view.overlay_cells` (`merge_overlay_cells` + recorder persistent layer).

## Forbidden

- Actual belt/pipe pre-install in void ([§0.2](00_core_principles.md))
- Saturating one goal then placing the next goal sequentially
- Laying transport in void and connecting afterward

Multiple goals from the start; distribute cost/load.

## Completion criteria

- [ ] `capacity_plan` records shape/fluid goal count derivation
- [ ] `PlannedRouteGoals` generated without transport materialization
- [ ] bilateral wide-face even spacing·rim distance policy is deterministic

## Required tests

```text
test_capacity_planner_estimates_extractor_groups_with_packing
test_capacity_planner_estimates_shape_goal_count_by_12
test_capacity_planner_estimates_fluid_goal_count_by_72
test_route_goal_distance_band_excludes_near_and_far_void
test_route_goals_bilateral_wide_faces_top_bottom_even_x
test_capacity_shape_goals_capped_by_extractor_scale
test_route_goal_planner_creates_multiple_external_margin_goals
test_route_goal_planner_does_not_materialize_transport
```

## Related code·documents

- Implementation: `django_apps/asteroid_lab/optimization/capacity_planner.py`, `route_goal_planner.py`
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) ? `RouteGoal`

## Next Phase

? [`phase_d_gene_templates.md`](phase_d_gene_templates.md)
