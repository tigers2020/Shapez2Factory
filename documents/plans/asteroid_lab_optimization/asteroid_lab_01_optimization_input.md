---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: plans/asteroid_lab_optimization snapshot — use documents/Algorithm/asteroid_lab_01_optimization_input.md
authority_for_implementation: documents/Algorithm/asteroid_lab_01_optimization_input.md
superseded_by:
  - documents/index/document_inventory.md
  - documents/ai/current_plan.md
last_reviewed: 2026-05-24
---

# Phase 1 — Optimization Input Contract

> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_01_optimization_input.md`](../../Algorithm/asteroid_lab_01_optimization_input.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Purpose

Convert reconstruction results into input DTOs the optimization layer can use stably.

## Input

Completed asteroid topology from the reconstruction engine.

Required semantics:

```text
extractor / extension removed coords = asteroid evidence
belt / pipe removed coords = not asteroid evidence
interior fill cell = asteroid field
void = exterior or true empty space
```

Existing layout is reflected in input as:

```text
existing belt / pipe / trunk / protected corridor
```

**belt vs pipe(kind)** is not re-inferred from coordinates alone. `RouteCellDomain.transport_mask` generation uses `existing_transport_cells` (or coord→kind derived from it) as primary source (Phase 4 builder).

## Coordinate authority (Island-local, PR-F)

See **Algorithm** doc. Summary: `CoordFrame.ISLAND_RAW`; dense server **removed**; `test_coordinate_frame_ast_gate.py` forbids `server_*` tokens in product code.

## Route goal contract

Using only `external_goals` at `frozenset[Coord]` level cannot distinguish trunk seed·corridor entry·margin·existing attachment·soft corridor, causing **STEP4-class recurrence**.

Therefore goals are fixed as **RouteGoal** units, not bare coordinates.

```python
# RouteGoalKind e.g.: trunk_seed | corridor_entry | external_margin |
# existing_transport_attachment | soft_corridor | (add on extension)
```

```python
@dataclass(frozen=True)
class RouteGoal:
    coord: Coord
    goal_kind: RouteGoalKind
    transport_kind: TransportKind | None
    priority: int
    existing_trunk: bool
```

Priority (default assumption for cost·feasibility interpretation):

```text
existing trunk connection
> soft corridor connection
> external margin connection
> asteroid carve
```

Detail costs align with Phase 4 `RouteCellDomain.traversal_cost` and probe policy.

### `RouteGoal.priority` ordering rule

**Fixed: smaller number = preferred (preferred match·lower penalty).** Prevent implementers interpreting “higher value is better.”

Example bands (project-tunable, but **direction** preserved):

```text
0  = existing trunk attachment·trunk_seed class
10 = soft_corridor / existing_transport_attachment
20 = external_margin
30 = asteroid carve allowed region etc.
```

`reached_goal` selection when cost vs `RouteGoal.priority` conflict is unified in Phase 4 `route_selection_score`·tie-break. Phase 1 `priority` fixes only **smaller-is-preferred** meaning.

## Topology graph contract

Cell sets alone cause routing·corridor·fitness to repeatedly call **island map grid** neighbor utils (e.g. `grid_contract.neighbors4`).

**TopologyGraph** is built once at reconstruction completion and placed in `OptimizationInput` as common input for later search·analysis.

```python
@dataclass(frozen=True)
class TopologyNode:
    coord: Coord
    node_kind: TopologyNodeKind

@dataclass(frozen=True)
class TopologyEdge:
    a: Coord
    b: Coord
    edge_kind: EdgeKind
    traversal_cost: int
```

**Undirected contract (v0):** `TopologyGraph` edges are **logically undirected**. Store both (a,b)·(b,a) **or** adjacency builder expands one pair bidirectionally. BFS·probe interpret **adjacency as undirected** (do not assume directed graph).

Alternatively keep same meaning with field names `src`/`dst`, but fix **undirected** in docs·tests as above.

```python
@dataclass(frozen=True)
class TopologyGraph:
    nodes: frozenset[TopologyNode]
    edges: frozenset[TopologyEdge]
```

`TopologyNodeKind` / `EdgeKind` start narrow per project domain and extend.

## Output DTO

For `@dataclass(frozen=True)` and **snapshot·hash·serialization stability**, do not put mutable `dict` directly in `existing_transport`. With no standard `FrozenMapping`, fix one of below (project picks one only).

```python
@dataclass(frozen=True)
class ExistingTransportCell:
    coord: Coord
    transport_kind: TransportKind
```

Recommended:

```python
existing_transport_cells: frozenset[ExistingTransportCell]
```

**Trunk authority:** only `existing_trunk_cells: frozenset[Coord]` grounds trunk membership. Do not put trunk flag on `ExistingTransportCell` (same as Overview).

Builder ensures one `TransportKind` per `coord` when creating `OptimizationInput`. If views·probe need `coord -> kind`, build derived `Mapping`; **DTO body prefers immutable sets**.

```python
@dataclass(frozen=True)
class OptimizationInput:
    asteroid_cells: frozenset[Coord]
    mineable_cells: frozenset[Coord]
    rim_cells: frozenset[Coord]
    interior_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    route_goals: frozenset[RouteGoal]
    existing_transport_cells: frozenset[ExistingTransportCell]
    existing_trunk_cells: frozenset[Coord]
    protected_corridor_cells: frozenset[Coord]
    blocked_cells: frozenset[Coord]
    topology_graph: TopologyGraph
    bbox: BBox
```

**Backward compatibility (docs only):** if legacy name `existing_transport_by_coord` remains in code, content must be read-only view like `MappingProxyType` or derived only from `existing_transport_cells`.

`blocked_cells` may remain **hard no-go** aggregate in v0. Adapter / domain builder is responsible for syncing without contradiction to Phase 4 `RouteCellDomain.hard_blocked`.

### `protected_corridor_cells` and `route_domain`

All coords in `protected_corridor_cells` must be **included in the key set of `RouteCellDomain` produced by subsequent `route_domain` builder** (forbidden to list coords absent from domain). Detail follows Phase 4 builder contract.

## `route_domain` snapshot ownership (drift prevention)

**Search authority route_domain snapshot** as `Mapping[Coord, RouteCellDomain]` is created **only by `RouteDomainSnapshotBuilder` (single entry point)**.

```text
Input: immutable snapshot from OptimizationInput + (in commit loop) CONFIRMED RouteReservation·placement occupied etc. documented accumulated state
Forbidden: candidate generator·probe·evolution patching RouteCellDomain in-place
Recommended: after reservation append / successful commit, always full rebuild for next snapshot
```

Without exception **one builder** owns `hard_blocked`·`transport_mask`·`traversal_cost` consistency. Cross-reference Phase 4 input contract·Phase 7 commit loop.

## Coordinate rules

This plan and all layers after `OptimizationInput` use **`Coord` = (island x, island y)** only. Integer **dense grid** (…, -1, 0, 1, …); cardinal neighbors `(x±1, y)`, `(x, y±1)`.

Reconstruction·snapshot adapter puts only `Coord` satisfying this contract into `OptimizationInput`.

Required utility (`Coord` = island map):

```python
grid_contract.neighbors4(coord, frame) -> tuple[Coord, ...]
cardinal_unit_toward(src: Coord, dst: Coord) -> Direction
```

`grid_contract.neighbors4` is **standard 4-direction** dense rule. Align with `topology_graph` edges·probe fallback neighbor listing **same contract**. Edge set and neighbor util have **single source**.

## Invariant

```text
[ ] All Coord·cell sets island-local (x, y) (`grid_contract.neighbors4` dense 4-neighbor contract)
[ ] topology_graph·probe neighbors same contract as `grid_contract.neighbors4`
[ ] inferred interior fill must be mineable asteroid field
[ ] external void must not be mineable
[ ] belt/pipe removed positions must not become asteroid evidence by default
[ ] extractor/extension removed positions must become asteroid evidence
[ ] route_goals: each goal has goal_kind·priority·existing_trunk semantics
[ ] topology_graph: node coords do not contradict asteroid / void contract
[ ] existing_transport_cells: at most one cell record per coord (empty frozenset = greenfield no transport)
[ ] existing_trunk_cells ⊆ { c.coord for c in existing_transport_cells } (forbidden: trunk coord without transport kind)
[ ] `RouteGoalKind.existing_transport_attachment` class goals do not contradict kind in `existing_transport_cells`
[ ] all coords in protected_corridor_cells exist in route_domain builder output keys (Phase 4)
[ ] if existing_trunk / protected impossible overlap with mineable, adapter resolves with explicit policy
```

## Tests

```text
test_optimization_input_preserves_inferred_fill_as_mineable
test_optimization_input_marks_rim_cells
test_optimization_input_route_goals_touch_external_void_or_trunk_contract
test_optimization_input_transport_removed_not_asteroid_evidence
test_optimization_input_topology_graph_adjacency_matches_neighbors4
test_optimization_input_existing_transport_sets_transport_mask_inputs
test_optimization_input_existing_transport_unique_coord
test_optimization_input_greenfield_is_empty_transport_and_trunk_and_protected
test_optimization_input_trunk_cells_subset_of_transport_cells
```

## Completion criteria

```text
[ ] OptimizationInput DTO implemented (route_goals·topology_graph·existing_transport_cells·trunk·protected included)
[ ] Reconstruction → OptimizationInput adapter + **RouteDomainSnapshotBuilder** seed path (same scope as dev sequence 1B)
[ ] island 4-neighbor(`grid_contract.neighbors4`) tests pass
[ ] hole asteroid etc. topology adapter validation completion criteria split to sequence 1B (dev sequence 10)
```

## Implementation contract — enums not free strings

The following values are fixed as **enums, not free strings**. Text lists in docs (Phase 3·4·8) match member names.

```text
RouteGoalKind
RouteProbeFailureReason
CandidateRejectReason
ValidationIssueCode
ValidationSeverity
EvolutionConvergenceReason
CommitConflictReason
OptimizationReplayEventType
ReservationState
PlacementCommitState
TransportMask
RouteClass
```

Phase 4·6·7·9 docs are authority for each type·enum. Phase 1 maintains **no free strings** principle and cross-references only.
