# Layer 03 — Rim Mining Bundle Candidate Expansion — Design Spec

**Document type:** Solver / Lab contract (Layer 3 candidate generation + route probe)  
**Status:** **APPROVED (2026-05-28)** — Hybrid Solver Contract Architect (§1–§3 + P0/P1 amendments)  
**Work classification:** contract change · implementation change  
**Scope:** `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/` · `layers/contracts/` · `layers/shared/route_probe.py` · `stack_runner` L2→L3 wiring  
**Extends:** [`2026-05-27-asteroid-lab-algorithm-layer-stack-design.md`](2026-05-27-asteroid-lab-algorithm-layer-stack-design.md) · [`2026-05-28-miner-seed-difficulty-rank-design.md`](2026-05-28-miner-seed-difficulty-rank-design.md) · [`2026-05-28-layer-02-exterior-connector-placement-design.md`](2026-05-28-layer-02-exterior-connector-placement-design.md)

**Korean title (reference):** L3 rim M-extractor 앵커 · void transport stub · route-probed dense candidate pool

**Implementation plans:** [`2026-05-28-layer-03-rim-mining-bundles-pr3a.md`](../plans/2026-05-28-layer-03-rim-mining-bundles-pr3a.md) · [`2026-05-28-layer-03-rim-mining-bundles-pr3b.md`](../plans/2026-05-28-layer-03-rim-mining-bundles-pr3b.md)

---

## §1 — Purpose and boundaries

### 1.1 Identity

| Item | Contract |
|------|----------|
| Slug | `layer_03_rim_mining_bundles` |
| Purpose | Expand **route-feasible** rim mining bundle **candidates** along `outer_rim_field` |
| Output | `RimBundleCandidateSet` + `Layer03ExpansionMetrics` |
| Dense coverage meaning | `dense candidate coverage` — **not** `dense committed layout` |

### 1.2 A′′ normative invariants

```text
anchor_coord ∈ outer_rim_field = field_rim_cells(complete_map.field_cells)
M extractor (mining) anchors on field rim cells
mining_occupied_cells ⊆ field_cells
transport_stub_cells ∩ field_cells = ∅
transport_stub_cells ⊆ exterior_transport_traversable (L3 virtual domain — see virtual-exterior-transport-domain spec)
mining_occupied_cells ∩ transport_stub_cells = ∅
transport_stub_cells must not be counted as extractor/extension footprint
route probe starts from route_probe_start_coord ∈ transport_stub_cells
probe targets RouteGoal view derived from L2 ExteriorConnectionPlan (not raw L2 DTO routing)
```

### 1.3 Forbidden (normative)

```text
Layer 3 MUST NOT mutate committed layout
Layer 3 MUST NOT commit placement (L5 incremental_commit only)
Layer 3 MUST NOT perform pool-wide non-overlap packing as a hard filter
Layer 3 MUST NOT use candidate enumeration order as Gene.commit_order
Layer 3 MUST NOT use difficulty_rank or seed_rank for pattern try order
Layer 3 MUST NOT use replay / NDJSON / solver_summary as algorithm input
Layer 3 MUST NOT treat candidate-stage route_probe success as commit guarantee
```

**Outer-rim greedy install (forbidden recurrence):**

```text
for rim_cell in rim_cells:
    if can_place_extractor:
        immediately commit extractor to layout   # FORBIDDEN
```

### 1.4 Facing policy — R2-lite (2026-05-28)

```text
R2-lite (2026-05-28): enumerate exterior_output_dir_candidates per anchor (≤4 cardinals).
L2 goal distance sorts enumeration order only.
See footprint-aware-exterior-direction-enumeration-design.md.
```

`select_exterior_output_dir` returns the first sorted candidate (compatibility helper). Expansion MUST enumerate all candidates via `exterior_output_dir_candidates`.

### 1.5 Pool overlap

```text
Candidates MAY overlap in occupied_cells across the pool.
Selection among overlaps is L4 / GA / L5 responsibility.
maximal_non_overlap_preview (optional observability) MUST NOT be algorithm input.
```

### 1.6 Stack inputs

| Input | Source |
|-------|--------|
| `ReconstructionCompleteMap` | L1 |
| `LayerBudgetContext` | `stack_runner` (60s cumulative L2–L5) |
| `ExteriorConnectionPlan \| None` | L2 |
| `MinerSeedCatalog` | `GeneticSample` `miner_seed_v2` default; test fixtures in-memory |

**L2 hold:** when `exterior_plan is None`, return empty pools with `rim_anchor_count` preserved and `layer_skip_reason = missing_exterior_connection_plan` (not all-zero metrics).

### 1.7 v0 transport scope

```text
One L3 run expands exactly one TransportKind (shape_belt OR fluid_pipe).
L3 v0 does not mix shape_belt and fluid_pipe in a single pass.
```

---

## §2 — DTOs and enums

### 2.1 Type layering

| Type | Role |
|------|------|
| `BundleCandidate` | identity + geometry + projection-time diagnostics |
| `RouteProbedBundleCandidate` | `candidate` + route_probe group (stack normative wrapper) |
| `RimBundleCandidateSet` | `normal_candidates` / `diagnostic_rejected_candidates` / `metrics` |

```text
route_probe fields MUST NOT be duplicated on BundleCandidate.
L5 MUST re-probe latest route_domain at commit time.
```

### 2.2 `ResourceKind` and `TransportKind`

```python
class ResourceKind(StrEnum):
    SHAPE = "shape"
    FLUID = "fluid"


class TransportKind(StrEnum):
    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"
```

```text
resource_kind and transport_kind MUST NOT be collapsed to a single free-form str.
L2 ExteriorConnectionPlan.transport_kind (shape|fluid) maps to ResourceKind at L3 boundary.
transport_kind = map_resource_kind_to_transport_kind(resource_kind)
```

### 2.3 `BundleCandidate` — identity

| Field | Type | Rule |
|-------|------|------|
| `candidate_id` | `str` | Deterministic; **not** commit order |
| `layer_slug` | literal | `layer_03_rim_mining_bundles` |
| `gene_key` | `str` | Source identity (may appear in `candidate_id`) |
| `pattern_id` | `str` | From seed metadata |
| `intrinsic_priority_rank` | `int` | 1..18; enumeration order only |
| `anchor_coord` | `Coord` | M extractor anchor |
| `output_dir` | `Direction` | R1-hardening fieldward |
| `rotation` | `int` | R0_E_CW after fieldward align |
| `resource_kind` | `ResourceKind` | |
| `transport_kind` | `TransportKind` | |
| `equivalence_key` | `str` | Semantic dedupe (§2.6) |

Recommended `candidate_id` format:

```text
layer_03:{gene_key}:{anchor_x}:{anchor_y}:{output_dir}:{rotation}:{transport_kind}
```

### 2.4 `BundleCandidate` — geometry

**Amended 2026-05-28 (weighted routing):** See [`2026-05-28-layer-03-weighted-transport-routing-design.md`](2026-05-28-layer-03-weighted-transport-routing-design.md).

| Field | Type | Invariant |
|-------|------|-----------|
| `mining_occupied_cells` | `frozenset[Coord]` | M + extensions; ⊆ `field_cells` |
| `transport_stub_cells` | `frozenset[Coord]` | seed-projected belt/pipe stubs (map absolute) |
| `route_probe_start_coord` | `Coord` | **transport_entry_coord** — first routing entry; ∉ `mining_occupied_cells`; **not** required ∈ `transport_stub_cells` |
| `placements` | `tuple[BundlePlacement, ...]` | Map-absolute coords (§2.4.1) |
| `throughput_factor` | `int` | 4 \| 8 \| 12 \| 16 |
| `topology_signature` | `str` | From seed metadata; optional in equivalence |

**Field transport (normative):** Belt/pipe MAY occupy `field_cells`. M/E has priority: `mining_occupied_cells` are transport hard blockers. Field routes are high-cost fallback (weighted probe).

**Korean reference:**

```text
asteroid field는 belt/pipe 금지 영역이 아니다.
belt/pipe는 field 위에도 설치 가능하다.
다만 M/E가 field 사용 우선권을 가지므로,
M/E occupied cell은 transport hard blocker이고,
field 위 transport는 높은 비용/낮은 우선순위로 처리한다.
```

`BundlePlacement`:

```python
class BundleCellRole(StrEnum):
    MINER = "miner"
    EXTENSION = "extension"
    TRANSPORT_STUB = "transport_stub"


@dataclass(frozen=True, slots=True)
class BundlePlacement:
    coord: Coord
    layout_t: str
    rotation: int
    cell_role: BundleCellRole
```

#### 2.4.1 Coordinate frame

```text
BundlePlacement.coord is map-absolute in complete_map.coord_frame (v1: ISLAND_RAW).
Seed-local offsets MUST stay inside project.py and MUST NOT leak onto BundleCandidate.
Forbidden: storing canonical seed-relative offsets on BundleCandidate.
```

### 2.5 `RouteProbedBundleCandidate` — route probe

```python
class RouteProbeStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED_BUDGET = "skipped_budget"
    SKIPPED_GEOMETRY = "skipped_geometry"
    SKIPPED_NO_GOAL = "skipped_no_goal"  # reserved; v0 early-exit uses layer_skip_reason
```

| Field | Rule |
|-------|------|
| `route_probe_status` | StrEnum above |
| `route_probe_result` | Required non-`None` iff `SUCCEEDED` |
| `route_goal_id` | `str \| None`; non-`None` iff `SUCCEEDED` |
| `reject_reason` | `CandidateRejectReason \| None` on failure/skip |

`RouteProbeResult` (minimal v0):

```text
reached_goal: bool
goal_coord: Coord | None
path_coords: tuple[Coord, ...]   # bounded feasibility path, not optimal
steps_expanded: int
transport_kind: TransportKind
```

**Path shape (stored on `RouteProbeResult` only):**

```text
path_coords[0] == route_probe_start_coord
If reached_goal: path_coords[-1] == goal_coord
```

**Validation location (normative):** `RouteProbeResult` has no `route_probe_status`. Endpoint and `SUCCEEDED` coupling are enforced on `RouteProbedBundleCandidate.__post_init__` and in `build_rim_bundle_candidate_set`:

```text
If route_probe_status == SUCCEEDED:
  route_probe_result is not None
  route_goal_id is not None
  path_coords[0] == candidate.route_probe_start_coord
  path_coords[-1] == route_probe_result.goal_coord
```

### 2.6 Equivalence and dedupe

```text
candidate_id  = source identity (may include gene_key)
equivalence_key = semantic geometry/effect identity (gene_key EXCLUDED)

equivalence_key = stable_hash(
  transport_kind,
  resource_kind,
  output_dir,
  throughput_factor,
  route_probe_start_coord,
  sorted(mining_occupied_cells),
  sorted(transport_stub_cells),
  topology_signature,
)
```

**On `SUCCEEDED` before append to normal pool:**

```text
If equivalence_key already seen:
  dedupe_duplicate_count += 1   # ALWAYS, including winner replacement
  If new intrinsic_priority_rank < incumbent: replace winner
  Elif equal rank and new.candidate_id < incumbent.candidate_id: replace winner
  Else: keep incumbent
Else:
  register winner in best_by_equivalence

normal_candidate_count == len(unique equivalence keys in normal pool)
```

```text
DUPLICATE_EQUIVALENCE MUST NOT append a diagnostic row; metrics only.
```

### 2.7 `CandidateRejectReason`

```python
class CandidateRejectReason(StrEnum):
    NO_EXTERIOR_VOID_NEIGHBOR = "no_exterior_void_neighbor"
    NO_ROUTE_GOAL_FOR_TRANSPORT_KIND = "no_route_goal_for_transport_kind"
    LOCAL_GEOMETRY_INVALID = "local_geometry_invalid"
    MINING_CELL_OFF_FIELD = "mining_cell_off_field"
    TRANSPORT_STUB_NOT_IN_VOID = "transport_stub_not_in_void"
    ROUTE_PROBE_FAILED = "route_probe_failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
```

### 2.8 `RouteGoal` view

```python
class RouteGoalKind(StrEnum):
    EXTERIOR_CONNECTOR_VOID = "exterior_connector_void"


ROUTE_GOAL_PRIORITY_REQUIRED = 0
ROUTE_GOAL_PRIORITY_SPARE = 10


@dataclass(frozen=True, slots=True)
class RouteGoal:
    goal_id: str
    kind: RouteGoalKind
    coord: Coord
    transport_kind: TransportKind
    priority: int
    connector_role: ExteriorConnectorRole
```

```text
build_layer03_route_goals(exterior_plan, *, transport_kind) -> tuple[RouteGoal, ...]
  Filter planned_connectors to those mapping to transport_kind.
  priority = 0 if role==REQUIRED else 10
  Sort by (priority, goal_id) for deterministic probe order.
```

L3 MUST NOT interpret `ExteriorConnectionPlan` routing semantics directly beyond this builder.

### 2.9 `Layer03ExpansionMetrics`

| Field | Meaning |
|-------|---------|
| `rim_anchor_count` | `len(outer_rim_field)` |
| `seed_projection_attempt_count` | anchor × seed projection tries |
| `local_geometry_rejected_count` | geometry fail |
| `route_probe_attempt_count` | probe calls |
| `route_probe_succeeded_count` | `SUCCEEDED` |
| `route_probe_failed_count` | `FAILED` |
| `dedupe_duplicate_count` | duplicate equivalence hits |
| `normal_candidate_count` | `len(normal_candidates)` |
| `diagnostic_rejected_count` | `len(diagnostic_rejected_candidates)` — assign once at end |
| `budget_skipped_count` | `SKIPPED_BUDGET` |
| `layer_skip_reason` | `Layer03SkipReason` |

```python
class Layer03SkipReason(StrEnum):
    NONE = "none"
    MISSING_EXTERIOR_CONNECTION_PLAN = "missing_exterior_connection_plan"
    NO_ROUTE_GOALS = "no_route_goals"
    BUDGET_EXHAUSTED = "budget_exhausted"
```

**Pool invariant (normative):**

```text
∀ c ∈ normal_candidates: c.route_probe_status == SUCCEEDED
Unprobed / SKIPPED_* / FAILED MUST NOT appear in normal_candidates
```

### 2.10 `run_layer_03` signature

```python
def run_layer_03_rim_mining_bundles(
    *,
    complete_map: ReconstructionCompleteMap,
    exterior_plan: ExteriorConnectionPlan | None,
    budget_ctx: LayerBudgetContext,
    seed_catalog: MinerSeedCatalog | None = None,
    resource_kind: ResourceKind | None = None,
) -> RimBundleCandidateSet:
```

```text
# After exterior_plan is confirmed non-None (see §3.1):
derive_layer03_resource_kind(exterior_plan, explicit resource_kind)
transport_kind = map_resource_kind_to_transport_kind(resource_kind)
route_goals = build_layer03_route_goals(exterior_plan, transport_kind=transport_kind)
```

---

## §3 — Runtime

### 3.1 Enumeration (normative)

```text
outer_rim ← field_rim_cells(complete_map.field_cells)
metrics.rim_anchor_count ← len(outer_rim)

IF exterior_plan is None:
  RETURN empty pools, layer_skip_reason=MISSING_EXTERIOR_CONNECTION_PLAN

resource_kind ← derive_layer03_resource_kind(exterior_plan, explicit resource_kind)
transport_kind ← map_resource_kind_to_transport_kind(resource_kind)
route_goals ← build_layer03_route_goals(exterior_plan, transport_kind=transport_kind)

IF route_goals is empty:
  RETURN empty pools, layer_skip_reason=NO_ROUTE_GOALS

FOR anchor IN sorted(outer_rim_field, key=(y, x)):
  IF budget_ctx.remaining_budget_ms() <= 0:
    layer_skip_reason ← BUDGET_EXHAUSTED
    BREAK   # no diagnostic candidate

  output_dir ← select_fieldward_output_dir(anchor, ..., transport_kind)
  IF output_dir is None:
    append diagnostic(SKIPPED_GEOMETRY, NO_EXTERIOR_VOID_NEIGHBOR)
    CONTINUE

  FOR seed IN catalog.by_intrinsic_priority_rank():
    IF budget_ctx.remaining_budget_ms() <= 0 at anchor boundary:
      layer_skip_reason ← BUDGET_EXHAUSTED; BREAK

    seed_projection_attempt_count += 1
    projection ← project_miner_seed_at_anchor(...)
    IF projection.candidate is None:
      local_geometry_rejected_count += 1
      append diagnostic(SKIPPED_GEOMETRY, projection.reject_reason)
      CONTINUE
    candidate ← projection.candidate

    IF budget exhausted after projection, before probe:
      append diagnostic(SKIPPED_BUDGET)
      budget_skipped_count += 1
      layer_skip_reason ← BUDGET_EXHAUSTED
      BREAK

    route_probe_attempt_count += 1
    probed ← immediate_route_probe(...)
    handle SUCCEEDED / FAILED / SKIPPED_BUDGET per §2.6 and §3.2

normal_candidates ← values(best_by_equivalence) sorted deterministically
diagnostic_rejected_count ← len(diagnostic_rejected_candidates)
```

### 3.2 Budget semantics

```text
60s cap owned exclusively by stack_runner.

route_probe_attempt_count increments only when immediate_route_probe is invoked.
Geometry validation and projection do NOT increment route_probe_attempt_count.

Wall-clock: projection and geometry still consume real time.
L3 MUST check remaining_budget_ms at anchor-loop entry and before each route probe.
```

| Event | Behavior |
|-------|----------|
| Budget exhausted at anchor boundary (no current candidate) | `layer_skip_reason=BUDGET_EXHAUSTED`; break; **no** diagnostic |
| Budget exhausted after projection / during probe | `SKIPPED_BUDGET` diagnostic for current candidate; `budget_skipped_count++`; break |

```text
budget slot (route_probe_attempt_count) ≠ wall-clock budget (remaining_budget_ms)
```

Probe bound: `steps_expanded ≤ LAYER03_ROUTE_PROBE_MAX_STEPS` (const + tests).

### 3.3 Projection result (PR-3b)

```python
@dataclass(frozen=True, slots=True)
class ProjectionResult:
    candidate: BundleCandidate | None
    reject_reason: CandidateRejectReason | None
```

```text
project_miner_seed_at_anchor(...) -> ProjectionResult
  (not bare BundleCandidate | None)

On failure: candidate is None, reject_reason is non-None.
On success: candidate is non-None, reject_reason is None.
```

### 3.4 `MinerSeedCatalog`

```python
@dataclass(frozen=True, slots=True)
class MinerSeedEntry:
    gene_key: str
    pattern_id: str
    intrinsic_priority_rank: int
    throughput_factor: int
    topology_signature: str
    decoded_json: dict[str, Any]


@dataclass(frozen=True, slots=True)
class MinerSeedCatalog:
    seeds: tuple[MinerSeedEntry, ...]  # sorted intrinsic_priority_rank ascending
```

| Rule | |
|------|--|
| Default loader | ORM `GeneticSample` `miner_seed_v2` + `is_seed=true` |
| Order | `intrinsic_priority_rank` only |
| Forbidden runtime input | `var/default_miner_pattern.txt` |
| Pattern projection | `layer_03_rim_mining_bundles/project.py` only (defer `shared/pattern_project.py` until L4 proves duplication) |

### 3.5 Package layout

```text
layers/contracts/candidates.py
layers/contracts/route_goal.py
layers/shared/route_probe.py
layers/layer_03_rim_mining_bundles/
  run.py
  expand.py
  rim_anchors.py
  seed_catalog.py
  project.py
  route_goals.py
```

### 3.6 Stack runner patch

```text
run_layers_02_to_05 passes ExteriorConnectionPlan | None from L2 into L3 run signature.
L3 post-summary emits Layer03ExpansionMetrics wire subset.
```

### 3.7 Non-goals (v0)

```text
R2 multi-void-edge, R3 cardinal-4
pool-wide non-overlap hard filter
Layer 04 inner fill (separate plan)
GA, incremental commit, validation
shared/pattern_project.py until L4 duplication proven
mixed shape_belt + fluid_pipe in one L3 pass
```

---

## §4 — Related documents

| Doc | Relationship |
|-----|----------------|
| [`2026-05-27-asteroid-lab-algorithm-layer-stack-design.md`](2026-05-27-asteroid-lab-algorithm-layer-stack-design.md) | Layer table, `RimBundleCandidateSet` shape, pool invariant |
| [`2026-05-28-miner-seed-difficulty-rank-design.md`](2026-05-28-miner-seed-difficulty-rank-design.md) | `intrinsic_priority_rank` consumer boundary |
| [`documents/Algorithm/asteroid_lab_00_overview.md`](../../../documents/Algorithm/asteroid_lab_00_overview.md) | Rim ≠ install order; forbidden greedy recurrence |
| [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) | Forbidden shortcuts (enumeration ≠ commit order) |
| [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](2026-05-28-layer-03-virtual-exterior-transport-domain-design.md) | Virtual exterior `placeable_cells` vs explicit `path_coords` transport network (§3.6) |

---

## Approval record

```text
2026-05-28 — §1–§3 APPROVED (Hybrid Solver Contract Architect)
  A′′ rim M-anchor + void transport
  R1-hardening fieldward
  P0: ResourceKind/TransportKind order, budget wall-clock vs probe slot,
      dedupe_duplicate_count semantics, SKIPPED_BUDGET diagnostic rules
  P1: early NO_ROUTE_GOALS exit, diagnostic_rejected_count at end

2026-05-28 — Doc patch (pre PR-3a implementation)
  P0: exterior_plan None before resource_kind/route_goals
  P0: RouteProbe SUCCEEDED validation on RouteProbedBundleCandidate / factory
  P0: equivalence_key builder excludes gene_key (tests use two candidates)
  P0: ProjectionResult for project_miner_seed_at_anchor
```
