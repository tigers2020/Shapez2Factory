---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: G
pr: 2
related_docs:
  - documents/Algorithm/asteroid_lab_04_route_probe.md
  - documents/Algorithm/solver_runtime/open_decisions.md
---

# Phase G ? Route Probe

## Purpose

Quickly check whether candidate can connect from `route_probe_start` to `RouteGoal`. **Feasibility only**, not global optimal routing.

## Input

```python
RouteProbeInput(
    start=projected.route_probe_start,
    goals=planned_route_goals,
    route_domain=route_domain,
    topology_graph=inp.topology_graph,
    max_expansions=config.route_probe_max_expansions,
    transport_kind=transport_kind,
    goal_priority_weight=10,
)
```

**Legacy difference:** [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md) `output_stub` = **forbidden alias**; Runtime?new code uses **`route_probe_start`** only ([§0.6](00_core_principles.md), [OD-1](open_decisions.md)).

## Output

```python
RouteProbeResult(
    reachable=True/False,
    path=...,
    cost=...,
    expanded_nodes=...,
    reached_goal=...,
    goal_priority=...,
    failure_reason=...,
)
```

## Tasks

### Route domain (candidate phase)

At candidate stage, `projected.occupied_cells` are **not yet confirmed (commit) ownership** ? probe reflects them as **provisional blockers** only.

**Recommended API (PR2):** `RouteDomainSnapshotBuilder.build_snapshot` adds candidate-phase occupancy factor.

```python
def build_route_domain_for_projected_gene_probe(builder, inp, projected):
    return builder.build_snapshot(
        inp,
        provisional_blocked_cells=projected.occupied_cells,
    )
```

**Implementation:** `build_route_domain_for_projected_gene_probe` ? `build_snapshot(..., provisional_blocked_cells=...)`. Do not use `committed_occupied_cells` for provisional.

Wrapper?call site **function docstring:**

```text
Candidate-phase provisional occupancy only. This does not commit placement.
```

`RouteDomainSnapshotBuilder` **single** entry point ? in-place mutation forbidden.

### Search

- v0 unit-cost domain: **bounded BFS** fast path
- non-uniform `traversal_cost`: bounded uniform-cost (heap)
- `hard_blocked` skip
- `transport_mask` mismatch skip
- goal `transport_kind` filter
- candidate phase: reverse distance-map prefilter (unreachable stub reject) then full probe for survivors
- `RouteDomainSnapshotBuilder` seed cells cached per `OptimizationInput` signature; overlays always new dict

### Goal selection

```text
route_selection_score = path_cost + goal_priority_weight * goal.priority
```

Tie-break:

```text
path_cost asc
priority asc
goal.coord lexicographic
goal_kind fixed order
```

## Forbidden

- Using candidate probe success as commit proof ([§0.5](00_core_principles.md))
- Probe materializing belt/pipe in layout

## Completion criteria

- [ ] reachable ? `reached_goal` non-null
- [ ] blocked?mask?budget exceeded recorded as enum `failure_reason`
- [ ] search starts only from `route_probe_start` (not fixed_output_transport as start)

## Prerequisite phase

```text
test_route_probe_reaches_goal_on_open_domain
test_route_probe_returns_no_goal_cells_when_filtered_goals_empty
test_route_probe_respects_hard_blocked_cells
test_route_probe_respects_transport_mask
test_route_probe_budget_exceeded
test_route_probe_selects_goal_by_priority_weighted_score
test_route_probe_uses_route_probe_start_not_fixed_output_transport
test_route_probe_bfs_matches_uniform_cost_on_unit_cost_domain
test_seed_domain_cache_reuses_seed_and_overlay_is_independent
```

## Related code?documents

- Implementation: `django_apps/asteroid_lab/optimization/route_probe.py`
- [`asteroid_lab_04_route_probe.md`](../asteroid_lab_04_route_probe.md)

## Next Phase

? [`phase_h_candidate_pool.md`](phase_h_candidate_pool.md)
