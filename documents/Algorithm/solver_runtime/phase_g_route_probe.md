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

# Phase G ??Route Probe

## ëª©ì 

candidate??`route_probe_start`?ì„œ `RouteGoal`ê¹Œì? ?°ê²° ê°€?¥í•œì§€ ë¹ ë¥´ê²??‰ê??œë‹¤. ?„ì—­ ìµœì  routing???„ë‹ˆ??**feasibility**??

## ?…ë ¥

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

**?ˆê±°??ì°¨ì´:** [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md)??`output_stub` = **ê¸ˆì? alias**; RuntimeÂ·? ê·œ ì½”ë“œ??**`route_probe_start`** ë§?([Â§0.6](00_core_principles.md), [OD-1](open_decisions.md)).

## ?°ì¶œë¬?

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

## ?‘ì—…

### Route domain (candidate phase)

candidate ?¨ê³„ `projected.occupied_cells`??**?•ì •(commit) ?ìœ ê°€ ?„ë‹˜** ??probe??**provisional blocker**ë§?ë°˜ì˜?œë‹¤.

**ê¶Œì¥ API (PR2):** `RouteDomainSnapshotBuilder.build_snapshot`??candidate ?„ìš© ?¸ì ì¶”ê?.

```python
def build_route_domain_for_projected_gene_probe(builder, inp, projected):
    return builder.build_snapshot(
        inp,
        provisional_blocked_cells=projected.occupied_cells,
    )
```

**êµ¬í˜„:** `build_route_domain_for_projected_gene_probe` ??`build_snapshot(..., provisional_blocked_cells=...)`. `committed_occupied_cells`??provisional???£ì? ?ŠëŠ”??

wrapperÂ·call site **?„ìˆ˜ ì£¼ì„:**

```text
Candidate-phase provisional occupancy only. This does not commit placement.
```

`RouteDomainSnapshotBuilder` **?¨ì¼** ì§„ì… ??in-place mutation ê¸ˆì?.

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

## ê¸ˆì?

- candidate probe ?±ê³µ??commit ì¦ëª…?¼ë¡œ ?¬ìš© ([Â§0.5](00_core_principles.md))
- probeê°€ layout??belt/pipe materialize

## ?„ë£Œ ì¡°ê±´

- [ ] reachable ??`reached_goal` non-null
- [ ] blockedÂ·maskÂ·budget exceededê°€ enum `failure_reason`?¼ë¡œ ê¸°ë¡
- [ ] `route_probe_start`?ì„œë§??ìƒ‰ ?œì‘ (fixed_output_transport ?€?€ start ?´ì „)

## ?„ìˆ˜ ?ŒìŠ¤??

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

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- ?ˆì •: `django_apps/asteroid_lab/optimization/route_probe.py`
- [`asteroid_lab_04_route_probe.md`](../asteroid_lab_04_route_probe.md)

## ?¤ìŒ Phase

??[`phase_h_candidate_pool.md`](phase_h_candidate_pool.md)
