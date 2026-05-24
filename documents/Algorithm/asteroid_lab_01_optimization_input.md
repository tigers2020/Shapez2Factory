# Phase 1 — Optimization Input Contract

## Purpose

Convert reconstruction results into an input DTO that the optimization layer can use reliably.

## Input

Complete asteroid topology produced by the reconstruction engine.

Required semantics:

```text
extractor / extension removed coords = asteroid evidence
belt / pipe removed coords = not asteroid evidence
interior fill cell = asteroid field
void = exterior or true empty space
```

The existing layout is reflected in the input as follows:

```text
existing belt / pipe / trunk / protected corridor
```

**belt vs pipe (kind)** is not re-inferred from coordinates alone. `RouteCellDomain.transport_mask` generation uses `existing_transport_cells` (or coord→kind derived from it) as the primary source (Phase 4 builder).

## Coordinate canonical form (PR-F island-local, RTTP default)

**Lab RTTP (2026-05, PR-F):** `OptimizationInput.coord_frame` defaults to `ISLAND_RAW`. `Coord` is copy JSON island-local `(x, y)` (same as reconstruction cell `x`/`y`). `server_dense`·`SERVER_DENSE` runtime paths **removed**.

**Persist / fingerprint:** map layout v2·absolute v2·`_asteroid_lab_coord_system` = `island_bbox_left_bottom_raw_xy_v1` / `island_raw_xy_v1`. `server_x`/`server_y` JSON attach·`server_coords.py` **forbidden** (`attach_island_coord_meta_to_decoded_json` only).

**Forbidden:** raw↔server re-conversion or dense server bridge import inside optimization·candidate·probe·commit·validation. 4-neighbor uses `grid_contract.neighbors4` on island grid.

**History:** dense server coordinates — [`research_asteroid_server_coords_layout_fingerprint_2026-05-16.md`](../research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md) (ARCHIVED).

**Verification:** `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py`, `test_optimization_input_coord_frame.py`, `test_coord_proof_policy.py`, `test_import_boundaries.py`(shapez_asteroid).

## Route goal contract

Using only `external_goals` at the `frozenset[Coord]` level cannot distinguish trunk seed·corridor entry·margin·existing attachment points·soft corridor, leading to **STEP4-class recurrence**.

Therefore goals are fixed as **RouteGoal** units, not coordinates.

```python
# RouteGoalKind examples: trunk_seed | corridor_entry | external_margin |
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

Detailed costs are aligned with Phase 4 `RouteCellDomain.traversal_cost` and probe policy.

Phase C generates `route_goals` coords from **padded `external_void` with mineable BFS distance 3–5**, **even spacing on both sides of wide faces**, and throughput-based goal count ([`solver_runtime/phase_c_capacity_route_goals.md`](solver_runtime/phase_c_capacity_route_goals.md)).

### `RouteGoal.priority` ordering rule

**Lower numbers mean preferred (priority matching·lower penalty)** — fixed. Implementers must not interpret “higher value is better.”

Example bands (adjustable in the project, but **direction** must be preserved):

```text
0  = existing trunk attachment·trunk_seed class
10 = soft_corridor / existing_transport_attachment
20 = external_margin
30 = asteroid carve allowed zone, etc.
```

When cost vs `RouteGoal.priority` conflict, `reached_goal` selection is unified in **Phase 4** via `route_selection_score`·tie-break. Phase 1 `priority` fixes only the **“lower is preferred”** meaning.

## Topology graph contract

With cell sets alone, routing·corridor·fitness repeatedly call **Server grid** neighbor utilities (e.g. `neighbors4_server`).

**TopologyGraph** is built once at reconstruction completion and placed in `OptimizationInput` as common input for subsequent search·analysis.

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

**Undirected contract (v0):** `TopologyGraph` edges are **logically undirected**. Storage includes both (a,b)·(b,a), or the adjacency builder expands one pair into bidirectional adjacency. BFS·probe interpret **adjacency as undirected** (do not assume a directed graph).

Alternatively, to preserve the same meaning, use field names `src`/`dst` but fix **undirected** semantics in docs·tests as above.

```python
@dataclass(frozen=True)
class TopologyGraph:
    nodes: frozenset[TopologyNode]
    edges: frozenset[TopologyEdge]
```

`TopologyNodeKind` / `EdgeKind` start narrow and expand to match project domain.

## Output DTO

To align `@dataclass(frozen=True)` with **snapshot·hash·serialization stability**, do not put mutable `dict` directly in `existing_transport`. With no standard `FrozenMapping`, fix one of the following (pick exactly one in the project):

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

**Trunk canonical form:** only `existing_trunk_cells: frozenset[Coord]` is the basis for trunk membership. Do not put a trunk flag on `ExistingTransportCell` (same as Overview).

The builder guarantees one `TransportKind` per `coord` when creating `OptimizationInput`. If views·probe need `coord -> kind`, build a **derived** `Mapping`, but **DTO body prefers immutable sets**.

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
    asteroid_bbox: BBox
    route_domain_bbox: BBox
    bbox: BBox  # deprecated alias == route_domain_bbox
```

**BBox semantics (v0):**

```text
asteroid_bbox       = tight mineable topology extent
route_domain_bbox   = asteroid_bbox expanded by OUTER_VOID_PADDING (default 10)
bbox                = route_domain_bbox (transition alias)
external_void_cells = route_domain_bbox cells not occupied by decoded snapshot cells
```

**Backward compatibility (docs only):** if the legacy name `existing_transport_by_coord` remains in code, content must be a **read-only view** such as `MappingProxyType`, or derived only from `existing_transport_cells`.

`blocked_cells` may remain as a **hard no-go** aggregate in v0. Responsibility for **non-contradictory** sync with Phase 4 `RouteCellDomain.hard_blocked` lies with adapter / domain builder.

### `protected_corridor_cells` and `route_domain`

Every coord in `protected_corridor_cells` **must be included** in the key set of `RouteCellDomain` produced by the subsequent `route_domain` builder (forbidden to list coords absent from the domain). Detailed reflection follows Phase 4 builder contract.

## `route_domain` snapshot ownership (drift prevention)

The **search canonical route_domain snapshot** in the form `Mapping[Coord, RouteCellDomain]` is created **only** by **`RouteDomainSnapshotBuilder` (single entry point)**.

```text
Input: immutable snapshot based on OptimizationInput + (in commit loop) documented cumulative state such as CONFIRMED RouteReservation·placement occupied
Forbidden: candidate generator·probe·evolution patching RouteCellDomain in-place
Recommended: after reservation append / successful commit, always create the next snapshot via full rebuild

| Method | Purpose |
|--------|---------|
| `build_snapshot(...)` | **Canonical** — `confirmed_reservations`, `committed_occupied_cells`, `provisional_blocked_cells` |
| `build_seed_snapshot(inp)` | seed only (equivalent when all overlays empty in `build_snapshot`) |
| `build_route_domain_for_projected_gene_probe` | candidate provisional only (Phase 4) |
| `build_commit_snapshot` | optional deprecated wrapper — **unimplemented**; semantics live only in `build_snapshot` |
```

Without exception, **one builder** owns `hard_blocked`·`transport_mask`·`traversal_cost` consistency. Cross-reference Phase 4 input contract·Phase 7 commit loop.

## Coordinate rules

In this plan and all layers after `OptimizationInput`, use only **`Coord` = (Server X, Server Y)**. Integer **dense grid** (…, -1, 0, 1, …); cardinal neighbors are `(x±1, y)`, `(x, y±1)`.

Reconstruction·snapshot adapter puts only `Coord` satisfying this contract into `OptimizationInput`.

Required utilities (`Coord` = Server only):

```python
neighbors4_server(coord: Coord) -> tuple[Coord, ...]
cardinal_unit_toward(src: Coord, dst: Coord) -> Direction
```

`neighbors4_server` follows the **standard 4-direction** dense rule. Align with **same contract** as `topology_graph` edges·probe fallback neighbor listing. Edge set and neighbor utility have a **single source**.

## Invariant

```text
[ ] All Coord·cell sets use Server X/Y (`neighbors4_server` dense 4-way contract)
[ ] topology_graph·probe neighbors match `neighbors4_server` contract
[ ] inferred interior fill must be mineable asteroid field
[ ] external void must not be mineable
[ ] asteroid_bbox ⊆ route_domain_bbox; padded route domain when OUTER_VOID_PADDING applied
[ ] external_void_cells ⊆ cells(route_domain_bbox)
[ ] belt/pipe removed positions must not become asteroid evidence by default
[ ] extractor/extension removed positions must become asteroid evidence
[ ] route_goals: each goal has goal_kind·priority·existing_trunk semantics
[ ] topology_graph: node coords do not contradict asteroid / void contract
[ ] existing_transport_cells: at most one cell record per coord (empty frozenset = greenfield no transport)
[ ] existing_trunk_cells ⊆ { c.coord for c in existing_transport_cells } (forbidden: trunk coord without transport kind)
[ ] `RouteGoalKind.existing_transport_attachment` class goals do not contradict kind in `existing_transport_cells`
[ ] every coord in protected_corridor_cells exists in route_domain builder output keys (Phase 4)
[ ] if existing_trunk / protected overlap mineable impossibly, adapter resolves with explicit policy
```

## Tests

```text
test_optimization_input_preserves_inferred_fill_as_mineable
test_optimization_input_marks_rim_cells
test_optimization_input_route_goals_touch_external_void_or_trunk_contract
test_optimization_input_transport_removed_not_asteroid_evidence
test_optimization_input_topology_graph_adjacency_matches_neighbors4_server
test_optimization_input_existing_transport_sets_transport_mask_inputs
test_optimization_input_existing_transport_unique_coord
test_optimization_input_greenfield_is_empty_transport_and_trunk_and_protected
test_optimization_input_trunk_cells_subset_of_transport_cells
```

## Completion criteria

```text
[ ] OptimizationInput DTO implementation (includes route_goals·topology_graph·existing_transport_cells·trunk·protected)
[ ] Reconstruction → OptimizationInput adapter + **RouteDomainSnapshotBuilder** seed path (same scope as development sequence 1B)
[ ] Server dense neighbor (`neighbors4_server`) tests pass
[ ] hole asteroid etc. topology adapter verification separated to sequence 1B completion criteria (development sequence 10)
```

## Implementation contract — enum instead of strings

The following values are fixed as **enums, not free strings**. Text lists in docs (Phase 3·4·8) stay identical to member names.

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

Phase 4·6·7·9 docs are canonical for each type·enum. Phase 1 maintains only cross-reference to the **no free strings** principle.
