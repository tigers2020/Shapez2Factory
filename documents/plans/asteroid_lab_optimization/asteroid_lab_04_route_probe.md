---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: plans/asteroid_lab_optimization snapshot — use documents/Algorithm/asteroid_lab_04_route_probe.md
authority_for_implementation: documents/Algorithm/asteroid_lab_04_route_probe.md
superseded_by:
  - documents/index/document_inventory.md
  - documents/ai/current_plan.md
last_reviewed: 2026-05-24
---

# Phase 4 — Fast Route Feasibility Probe


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_04_route_probe.md`](../../Algorithm/asteroid_lab_04_route_probe.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Purpose

Quickly evaluate whether a BundleCandidate's output_stub can connect to the **RouteGoal** set.

This stage is not optimal routing.

```text
goal = feasibility
not global optimal route
```

## Relationship to `TopologyGraph`

`RouteProbeInput` limits search with **`route_domain`** (per-cell pass rules·cost) and **`goals`**.

**Adjacency source (v0 contract):**

- Default: enumerate neighbors using **undirected** adjacency from `topology_graph` (Phase 1). Combine `traversal_cost` with edge·node policy and domain.
- Coords without key in `route_domain` follow **domain boundary policy** below.
- If `topology_graph` empty or stub implementation, **fallback**: build neighbors with `grid_contract.neighbors4(coord, frame)`, guaranteeing **same adjacency (dense 4-way)** as Phase 1 tests.

Neither “topology only ignoring domain” nor “domain only ignoring graph” is allowed. **Candidate expansion neighbors follow graph rules; cell pass·cost·mask are `RouteCellDomain`.**

## Algorithm

v0 default is **bounded uniform-cost search (Dijkstra-lite)**. Finds **weighted minimum cost** per `RouteCellDomain.traversal_cost` (and edge weights). When all `traversal_cost == 1` in fixture, **same behavior as BFS**.

A* heuristic may be added later.

## `TransportMask`

Authority type for `RouteCellDomain.transport_mask` (free dict forbidden).

```python
class TransportMask(IntFlag):
    NONE = 0
    SHAPE_BELT = 1
    FLUID_PIPE = 2
    BOTH = SHAPE_BELT | FLUID_PIPE
```

Or equivalently:

```python
@dataclass(frozen=True)
class TransportMaskStruct:
    allow_shape_belt: bool
    allow_fluid_pipe: bool
```

Project adopts **one**. If probe `transport_kind` mismatches, do not expand into that cell.

## Route cell domain (replacing allowed / preferred / blocked)

Using only `allowed_cells` + `preferred_cells` + `blocked_cells` tri-split tends to cause **route permission drift** as implementation progresses.

Per-cell meaning is fixed as **`RouteCellDomain`**.

```python
@dataclass(frozen=True)
class RouteCellDomain:
    coord: Coord
    route_class: RouteClass
    traversal_cost: int
    hard_blocked: bool
    carve_allowed: bool
    transport_mask: TransportMask
```

```python
route_domain: Mapping[Coord, RouteCellDomain]
```

v0 may let domain builder produce **reduced domain** from `OptimizationInput` and occupied cells·transport kind. Keep this contract so v1 carve·reclaim·reserved path·congestion does not **replace DTO wholesale**.

**Builder ownership:** authority entry for `route_domain` snapshot creation is same as Phase 1 **`RouteDomainSnapshotBuilder`** (no differently named wrapper·single responsibility). probe·evolution do not **in-place modify** domain per cell.

### Domain boundary·goal filter (v0 policy)

Align below with **`RouteProbeFailureReason`·search skip rules**.

```text
start not in route_domain -> invalid_route_domain (or pick start_blocked; fix one in docs·tests)
neighbor coord not in route_domain -> skip expansion (do not record as failure)
goal.coord not in route_domain -> exclude that RouteGoal (goals filter stage)
after filter goals empty -> no_goal_cells
```

If using both `invalid_route_domain` and `start_blocked`: **start outside domain → `invalid_route_domain`**, start inside domain but blocked by `hard_blocked`/mask → **`start_blocked`**.

## Input DTO

```python
@dataclass(frozen=True)
class RouteProbeInput:
    start: Coord
    goals: frozenset[RouteGoal]
    route_domain: Mapping[Coord, RouteCellDomain]
    topology_graph: TopologyGraph
    max_expansions: int
    transport_kind: TransportKind
    goal_priority_weight: int
```

`goal_priority_weight` used in `route_selection_score`. v0 default `10` recommended (may inject from `CandidateGenerationConfig`).

`goals` uses only those where `RouteGoal.transport_kind` matches probe `transport_kind` (document policy for unspecified goals).

Search does not expand into cells that are `hard_blocked` or where `transport_mask` disallows current transport.

## Goal selection·`reached_goal` (cost vs priority)

`RouteGoal.priority`: **smaller is preferred** (Phase 1). Path search optimizes **minimum cost** first. Authority when they conflict (v0):

### Probe selection score (weighted score, v0 authority)

```text
route_selection_score(path, goal) = path_cost + goal_priority_weight * goal.priority
```

- `path_cost`: sum of domain `traversal_cost` (and edge weights if present, same rule).
- `goal_priority_weight`: `RouteProbeInput.goal_priority_weight` (non-negative int). v0 example default: `10` (tunable).

**Selection rule:** among reachable (path, goal) candidates, pick **minimum `route_selection_score`**.

**Tie-break (determinism required):** (1) `path_cost` ascending (2) `goal.priority` ascending (3) `goal.coord` lexicographic (4) fixed `goal_kind` order — implementation fixes one global order.

Connect this score to `reached_goal`·`RouteProbeResult.cost`·fitness route penalty **without contradiction** (Phase 5).

## Failure reason type

In implementation `failure_reason` is **`RouteProbeFailureReason | None`**. Text list below matches enum member names.

## Output DTO

```python
@dataclass(frozen=True)
class RouteProbeResult:
    reachable: bool
    path: tuple[Coord, ...]
    cost: int
    expanded_nodes: int
    reached_goal: RouteGoal | None
    goal_priority: int | None
    failure_reason: RouteProbeFailureReason | None
```

When `reachable=True`, `reached_goal` is `RouteGoal` selected by **selection score·tie-break** above.

`goal_priority` is copy of `reached_goal.priority`, same **smaller-is-preferred** rule as `RouteGoal.priority` (Phase 1). Used in fitness·validation to distinguish trunk attachment vs margin scratch.

When `reachable=False`, `reached_goal`·`goal_priority` are `None`, `failure_reason` required.

## Cost Model v0

Domain `traversal_cost` is primary. Example semantics:

```text
existing trunk cell = low cost
external void corridor = normal cost
asteroid carve = high cost or forbidden (carve_allowed)
occupied bundle cell = hard_blocked
hard protected = hard_blocked
wrong transport kind = transport_mask mismatch
```

## Failure Reason (`RouteProbeFailureReason`)

```text
start_blocked
no_goal_cells
exhausted
budget_exceeded
blocked_by_occupied
invalid_transport_kind
invalid_route_domain
```

### When to use `blocked_by_occupied`

Normal expansion: neighbor `hard_blocked`/mask mismatch is **skipped**, not raised as `blocked_by_occupied`. Use `blocked_by_occupied` only when:

```text
start is in route_domain but start cell itself is occupied-derived hard_blocked, or
all valid neighbors of start are occupied-derived hard_blocked so no expansion is possible
```

Otherwise search exhaustion is `exhausted`.

### Budget·`expanded_nodes` definition

- **`expanded_nodes`**: count of coords **popped from frontier and finalized** (do not count same coord re-finalized; fix one rule in implementation·tests).
- **`max_expansions`**: when above count **exceeds** `max_expansions`, stop search and return `budget_exceeded` (when valid goal not reached).

## Connection to incremental commit (preview)

After successful commit, **reserved path** is reflected in `route_domain` snapshot from `RouteDomainSnapshotBuilder` for next probe (Phase 1·7). Candidate-phase probe is “snapshot at that time”; must not drift without re-probe after commit.

## Feasibility vs commitability (optimism boundary)

`reachable=True` is feasibility in **that `RouteProbeInput.route_domain` snapshot**. In incremental commit loop, **reservation accumulation·corridor starvation·different transport mask** may fail the same candidate.

Therefore:

```text
candidate probe success ≠ logical implication of final commit success
```

Mitigation: **Phase 7 always re-probe with latest domain**, **Phase 5 fitness** conservative proxies route_fragility·shared corridor pressure etc. (`PenaltyMode.CONSERVATIVE`; 0 only when `OFF`), **Phase 8 validation** distributes checks.

## Invariant

```text
[ ] uniform-cost search does not expand into hard_blocked cells
[ ] neighbor listing consistent with topology_graph undirected contract (fallback: same as grid_contract.neighbors4)
[ ] shape belt and fluid pipe route domains are separated
[ ] reachable=True requires path length > 0 unless start is goal
[ ] when reachable=True, reached_goal·goal_priority filled per contract
[ ] when reachable=False, failure_reason is RouteProbeFailureReason (required)
[ ] goal_kind·priority match contracted goals, not “any external coord reached”
[ ] reached_goal selection determined by route_selection_score·tie-break
[ ] expanded_nodes·max_expansions definitions match implementation·tests
[ ] blocked_by_occupied used only under documented narrow conditions
```

## Tests

```text
test_route_probe_reaches_prioritized_route_goal
test_route_probe_rejects_blocked_start
test_route_probe_never_crosses_hard_blocked_cells
test_route_probe_respects_island_cardinal_adjacency
test_route_probe_budget_exceeded
test_route_probe_transport_kind_separation
test_route_probe_respects_transport_mask_per_cell
test_route_probe_result_records_reached_goal_and_priority
test_route_probe_selection_score_prefers_lower_score_over_path_cost
test_route_probe_expanded_nodes_matches_definition
test_route_probe_blocked_by_occupied_only_at_start_trap
```

## Completion criteria

```text
[ ] bounded uniform-cost search (Dijkstra-lite) implemented
[ ] RouteProbeInput / RouteProbeResult (route_domain·RouteGoal·topology_graph) implemented
[ ] TransportMask type defined
[ ] RouteProbeFailureReason enum + RouteProbeResult (reached_goal·goal_priority) implemented
[ ] route_selection_score·tie-break documented and tested
[ ] callable from candidate_generator
```
