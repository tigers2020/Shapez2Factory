# Layer 03 — Rim Greedy Placement (L3/L4 integration) — Design Spec

**Document type:** Solver / Lab contract (rim placement only)  
**Status:** **APPROVED (2026-05-29)** — amendments §2.2, §2.3, §5.1–5.3, §6 applied  
**Work classification:** contract change · implementation change  
**Scope:** `layer_03_rim_greedy_placement` · L4 disable · supersede legacy L3/L4 · replay/observability for L3 only  

**Out of scope (explicit):** downstream layer integration · inner fill · final commit validation · `route_domain` final confirmation · `ROUTED_CONFIRMED` lifecycle

**Supersedes:**

- `layer_03_rim_mining_bundles` (dense candidate pool + overlap-allowed enumeration)
- `layer_04_rim_bundle_placement` (non-overlap selection from pool)
- HEAD specs: `2026-05-28-layer-03-rim-mining-bundles-design.md`, `2026-05-28-layer-04-rim-bundle-placement-design.md`
- `documents/Algorithm/asteroid_lab_00_overview.md` §4 “outer-rim greedy immediate commit” **for rim-only provisional placement** (rim greedy is now allowed at L3; global “candidate-only rim” v0 wording is retired for this layer)

**Decision locked:** **A1** — new slug/package; L4 removed from stack runner; L4 deprecated shim with disabled result only (one PR).

---

## §1 — Identity and supersession

### 1.1 Canonical layer

| Item | Contract |
|------|----------|
| Slug | `layer_03_rim_greedy_placement` |
| Package | `django_apps/asteroid_lab/layers/layer_03_rim_greedy_placement/` |
| Purpose | Traverse ordered outer-rim anchors; attempt M/E seeds; **provisional** place on success; DPS-check reachability to exterior connectors; reserve successful probe paths; invalidate consumed/conflicting anchors; score variants in pass 2 |
| Not purpose | Inner asteroid optimization · full routing optimization · global search (GA/MWIS/MILP) · using replay/NDJSON as algorithm input |

### 1.2 Retired layers

| Retired slug | Retired behavior |
|--------------|------------------|
| `layer_03_rim_mining_bundles` | Candidate pool expansion without layout mutation |
| `layer_04_rim_bundle_placement` | Deterministic packing/selection from pool |

### 1.3 Provisional placement wording

Pass 1 “commit” means **in-layer provisional occupancy** (equipment cells + route reservation). It is **not** documented here as final layout commit or downstream confirmation.

---

## §2 — Stack change

### 2.1 Before / after

```text
Before:
  L2 → L3 rim_mining_bundles → L4 rim_bundle_placement → next layers

After:
  L2 → L3 rim_greedy_placement → next layers
```

`next layers` are unchanged by this spec; their inputs/contracts are **not** defined here.

### 2.2 `stack_runner` contract

| Change | Requirement |
|--------|-------------|
| Runners | Remove `LAYER_04_RIM_BUNDLE_PLACEMENT` from `_DEFAULT_RUNNERS` |
| L3 entry | Call `run_layer_03_rim_greedy_placement(...)` |
| L3 return type | `IntegratedRimGreedyResult` (not `RimBundleCandidateSet`) |
| Layer index map | **Layer 4 index inactive/reserved** in `_LAYER_INDEX`; **do not renumber** downstream indices in this PR |
| `completed_layer_slugs` | Must **not** include `LAYER_04_RIM_BUNDLE_PLACEMENT` for default runner |
| Post-summary | `build_layer03_post_summary_metrics` consumes `IntegratedRimGreedyResult` |

**Layer index contract (normative):**

```text
LAYER_04_RIM_BUNDLE_PLACEMENT remains index 4 in _LAYER_INDEX as inactive/reserved.
LAYER_03_RIM_GREEDY_PLACEMENT uses index 3.
Downstream layers keep indices 5 and 6 unchanged.
Active runner sequence: L2 → L3 greedy → L5 → L6 (L4 not executed).
```

### 2.3 `layer_slugs.py`

| Constant | Action |
|----------|--------|
| `LAYER_03_RIM_GREEDY_PLACEMENT` | Add canonical slug; **only** L3 slug in active runner tuple |
| `LAYER_03_RIM_MINING_BUNDLES` | **Not** in active runner tuple; legacy import may thin-delegate one PR; delegated result reports `canonical_layer_slug=layer_03_rim_greedy_placement`; emit deprecation warning/metric; **no** active behavior-catalog entry |
| `LAYER_04_RIM_BUNDLE_PLACEMENT` | Keep string for shim imports/tests; **not** in `LAYERS_02_TO_06` active tuple |
| `LAYERS_02_TO_06` | Replace L3 slug with greedy; omit L4 from active execution list |

---

## §3 — Layer 04 disable contract

Layer 04 has **no algorithmic authority**.

### 3.1 Allowed (one PR)

```python
# layer_04_rim_bundle_placement/run.py — deprecated shim only

def run_layer_04_rim_bundle_placement(*args, **kwargs) -> Layer04DisabledResult:
    return Layer04DisabledResult(
        status="DISABLED",
        reason="SUPERSEDED_BY_LAYER_03_RIM_GREEDY_PLACEMENT",
    )
```

- Deprecated import re-exports (`empty_layer04_*` → disabled result or thin delegate)
- Warning / metric emission (`layer04_disabled_total`)
- Tests that still import L4 module paths

### 3.2 Forbidden on L4

```text
placement selection
route probe
overlay mutation
candidate filtering
score computation
replay assembly authority
any non-empty ProvisionalLayoutOverlay production
```

L4 is a **dead layer**; all rim placement logic lives in L3.

### 3.3 `Layer04DisabledResult` (minimal)

| Field | Type | Notes |
|-------|------|-------|
| `status` | `Literal["DISABLED"]` | Fixed |
| `reason` | `str` | Stable code, e.g. `SUPERSEDED_BY_LAYER_03_RIM_GREEDY_PLACEMENT` |
| `provisional_overlay` | `ProvisionalLayoutOverlay.empty()` | Optional convenience for legacy callers |
| `replay_frames` | `()` | Empty |

---

## §4 — Layer 03 new responsibility

L3 owns the full former L3+L4 rim pipeline:

```text
outer rim anchor build + boundary traversal order
deterministic multi-start variants (4)
seed attempt ordering (intrinsic priority)
provisional placement state per variant
DPS reachability to L2 exterior connector goals
route reservation on successful probe
anchor consumed / invalidated tracking
pass 1 install loop
pass 2 read-only validation + score + best variant selection
IntegratedRimGreedyResult + replay/observability emission
```

### 4.1 RimAnchor

Built from `ReconstructionCompleteMap.field_cells` and `external_void_cells`.

```text
rim anchor = field cell with ≥1 4-neighbor in external_void
Only external_void_cells are valid void normals.
Interior void is not a rim output normal unless explicitly classified as exterior.
```

```python
@dataclass(frozen=True)
class RimAnchor:
    coord: Coord
    void_dirs: tuple[Direction, ...]  # cardinal void directions
    traversal_index: int
    rim_segment_id: str | int
```

- **Forbidden:** sorting `field_rim_cells()` as the traversal order.
- **Required:** `build_ordered_outer_rim_anchors()` assigns `traversal_index` via boundary walk.
- Corners: up to two `void_dirs`; try order is deterministic (edge continuity → estimated DPS distance to connector → fixed `Direction` enum order).

### 4.2 Seed orientation (void normal)

```text
M faces outward along chosen void direction
E chain grows inward (behind M)
```

Example: void `E` → `M output_dir = E`, E extension west of M.

### 4.3 Traversal variants (deterministic multi-start)

| Variant id | Order |
|------------|-------|
| `CW_TL` | Clockwise from top-left-ish anchor |
| `CCW_TL` | Counter-clockwise, same start |
| `CW_MID` | Clockwise from longest-edge midpoint start |
| `EDGE_INTERLEAVE` | N/E/S/W edge-interleaved walk |

Each variant runs an isolated pass 1 + pass 2. Winner: `max(pass2_score)`; tie-break: variant id lexicographic.

### 4.4 Local placement window

Deterministic bounds only (no random micro-maps):

```text
bounds = seed_footprint_bbox
       ∪ M_output_stub
       ∪ DPS_search_margin (RimGreedyPolicy.DEFAULT_DPS_SEARCH_MARGIN = 12)
       ∪ exterior_connector_goal_region (from L2 plan view)
```

`LocalPlacementWindow` is derived from anchor, `output_dir`, seed footprint, and map fingerprint.

### 4.5 Seed attempt order

```text
for anchor in variant.rim_order:
  if anchor in consumed or invalidated: continue
  for output_dir in ordered_void_dirs(anchor):
    for seed in seeds_by_intrinsic_priority:
      try_place(...)
```

Tie-break sort: `intrinsic_priority desc` → `M count desc` → `E count desc` → `footprint area asc` → `seed_id asc`.

### 4.6 Pass 1 — install loop

On each successful attempt:

```text
record CommittedRimSeedPlacement (PROVISIONAL in-layer)
occupied_equipment_cells += equipment cells
reserved_route_cells += dps_path_cells
consumed_anchor_cells += anchors inside footprint
invalidated_anchor_cells += anchors conflicting with placement or route
```

### 4.7 Route reservation

| Rule | Contract |
|------|----------|
| On DPS success | `reserved_route_cells |= path_cells` |
| New equipment | `equipment_cells ∩ reserved_route_cells` → hard reject |
| Transport on reserved | allowed when compatible merge policy says so |
| Same pass | treat `reserved_route_cells` as **hard blocker for equipment** only |

DPS answers: “can we reach connectors without blocking?” — not “is belt already installed?”

### 4.8 DPS cost model (probe)

| Class | Treatment |
|-------|-----------|
| Hard blockers | committed M/E cells · incompatible occupied · search outside window |
| Soft / high cost | asteroid field cells · existing reservations · narrow corridors |

**Legality split (normative):** equipment legality and transport path legality are evaluated separately. M/E equipment MUST remain on `field_cells`. Transport probe MAY traverse permitted `external_void_cells` / field path cells per `dps_policy` weights.

Field cells are traversable at high cost so routes prefer exterior void over cutting through inner field.

```python
# dps_policy.py
DEFAULT_DPS_SEARCH_MARGIN = 12
```

Tests MUST read margin via `RimGreedyPolicy`, not hard-coded literals in assertions.

Reuse: `layers/shared/route_probe.py` (`weighted_route_probe` / domain builder) with greedy-specific domain weights; constants may move to `layer_03_rim_greedy_placement/dps_policy.py`.

### 4.9 Validation sequence (per attempt)

```text
1. anchor available (not consumed / invalidated)
2. seed footprint on field
3. no equipment collision
4. M/E priority rule
5. M output stub open toward exterior void
6. DPS to exterior connector goals succeeds
7. path does not cross hard blockers
8. on success: provisional place + reserve + invalidate
```

### 4.10 Pass 2 — read-only (v0)

```text
re-validate all committed placements in final variant state
compute score
no placement repair
hard validation failure → variant_score = invalid
```

**v0 score:**

```text
if hard_fail: invalid
else: score = 2 * M_count + E_count - 0.05 * total_route_length
```

Extended penalties (unreachable M, congestion, orphans) are **v1**.

---

## §5 — State and result DTOs

### 5.1 `RimGreedyState` (per variant, mutable during pass 1)

```python
@dataclass
class RimGreedyState:
    variant_id: str
    committed_placements: list[CommittedRimSeedPlacement]
    occupied_equipment_cells: set[Coord]
    reserved_route_cells: set[Coord]
    consumed_anchor_cells: set[Coord]
    invalidated_anchor_cells: set[Coord]
    rejected_attempts: list[RimGreedyReject]
```

### 5.2 `IntegratedRimGreedyResult` (layer output)

```python
@dataclass(frozen=True)
class IntegratedRimGreedyResult:
    committed_placements: tuple[CommittedRimSeedPlacement, ...]
    rejected_attempts: tuple[RimGreedyReject, ...]
    occupied_equipment_cells: frozenset[Coord]
    reserved_route_cells: frozenset[Coord]
    provisional_overlay: ProvisionalLayoutOverlay  # source_layer = layer_03_rim_greedy_placement
    pass2_report: RimGreedyPass2Report
    winning_variant_id: str
    metrics: RimGreedyMetrics
    observability_events: tuple[RimGreedyObservationEvent, ...]
```

L3 emits replay **payloads/events only**. The central replay assembler owns frame materialization and ordering. L3 MUST NOT emit opaque frame id strings as algorithm output.

### 5.3 `CommittedRimSeedPlacement`

```python
@dataclass(frozen=True)
class RimGreedyScoreAtoms:
    miner_count: int
    extension_count: int
    route_length: int
    base_score: float

@dataclass(frozen=True)
class CommittedRimSeedPlacement:
    placement_id: str
    variant_id: str
    anchor: Coord
    output_dir: Direction
    seed_id: str
    miner_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    m_output_stub: Coord
    route_probe_path: tuple[Coord, ...]
```

Per-placement score atoms are **optional in v0**; when present use `RimGreedyScoreAtoms`. Aggregate scoring lives on `RimGreedyPass2Report` (v0).

### 5.4 `RimGreedyReject` + `RimGreedyRejectReason` (StrEnum)

| Reason | When |
|--------|------|
| `ANCHOR_ALREADY_CONSUMED` | anchor in consumed set |
| `ANCHOR_INVALIDATED` | anchor in invalidated set |
| `NO_VOID_NORMAL` | cannot derive output direction |
| `FOOTPRINT_OUT_OF_FIELD` | illegal footprint |
| `EQUIPMENT_COLLISION` | overlaps occupied equipment |
| `PRIORITY_RULE_VIOLATION` | M/E priority |
| `M_OUTPUT_BLOCKED` | stub not open to void |
| `DPS_UNREACHABLE` | no goal path |
| `ROUTE_CROSSES_HARD_BLOCKER` | path illegal |
| `ORIENTATION_MISMATCH` | void normal vs placement |

Free-form `reason` strings are **forbidden** in production paths.

### 5.5 Overlay source constant

```python
LAYER_03_GREEDY_SOURCE = "layer_03_rim_greedy_placement"
```

`ProvisionalLayoutOverlay.source_layer` MUST use this constant (replaces `layer_04_rim_bundle_placement` for rim output).

### 5.6 Legacy DTO handling

| Legacy | Action |
|--------|--------|
| `RimBundleCandidateSet` | No longer produced by stack L3; remove from `stack_runner` L3 branch; keep types until test migration completes |
| `Layer04RimPlacementResult` | Shim returns `Layer04DisabledResult` only |

---

## §6 — Replay and observability (L3 only)

Replay is **observation only** — never algorithm input.

### 6.0 `RimGreedyObservationEvent` (L3 output)

```python
@dataclass(frozen=True)
class RimGreedyObservationEvent:
    phase: RimGreedyObservationPhase  # StrEnum aligned with §6.1 names
    variant_id: str
    payload: RimGreedyObservationPayload  # typed union per phase
```

### 6.1 Event phases (assembler-owned; L3 supplies payloads)

```text
rim_greedy_begin
rim_anchor_probe
rim_seed_attempt_rejected
rim_seed_committed
rim_route_probe_success
rim_route_probe_failed
rim_pass1_complete
rim_pass2_validation
rim_greedy_complete
```

### 6.2 Inspector minimum

```text
committed M/E cells
rejected anchors (reason)
DPS probe path
reserved route cells
invalidated rim anchors
pass2 hard-fail locations
winning variant id
```

### 6.3 Post-summary metrics (minimum)

```text
rim_anchor_count
committed_placement_count
rejected_attempt_count
reserved_route_cell_count
winning_variant_id
pass2_score
layer_skip_reason (when L2 plan missing)
```

### 6.4 Layer behavior catalog

Update `LAYER_BEHAVIOR_BY_SLUG` for `layer_03_rim_greedy_placement`; remove or mark deprecated entries for old L3/L4 slugs.

### 6.5 Replay segment migration

- Retire `replay/layer03_segment.py` pool-windowing semantics tied to candidate pools.
- Add `replay/layer03_rim_greedy_segment.py` projecting greedy frames.
- L4 replay segment: **no new frames**; existing L4 segment tests may assert disabled/empty until removed.

---

## §7 — Module layout

```text
layer_03_rim_greedy_placement/
  __init__.py
  run.py                    # run_layer_03_rim_greedy_placement
  rim_anchors.py            # build_ordered_outer_rim_anchors, RimAnchor
  traversal_variants.py     # 4 variant builders
  seed_orient.py            # void normal → M/E layout
  greedy_pass1.py           # install loop + state updates
  greedy_pass2.py           # read-only validate + score
  dps_policy.py             # domain weights, margins
  local_window.py           # LocalPlacementWindow
  contracts.py              # or layers/contracts/rim_greedy.py
```

Shared probe stays in `layers/shared/route_probe.py`.

---

## §8 — Inputs

| Input | Source |
|-------|--------|
| `ReconstructionCompleteMap` | L1 |
| `ExteriorConnectionPlan \| None` | L2 |
| `LayerBudgetContext` | `stack_runner` |
| `MinerSeedCatalog` | genetic sample / fixture |
| `ResourceKind`, `TransportKind` | one transport kind per run (v0) |
| `RimGreedyPolicy` | optional constants (margins, variant enablement) |

**L2 hold:** if `exterior_plan is None`, return empty `IntegratedRimGreedyResult` with `layer_skip_reason = missing_exterior_connection_plan` and `rim_anchor_count` preserved where cheap to compute.

---

## §9 — Testing (contract-level)

| Test | Oracle |
|------|--------|
| Boundary traversal order | Same map → same `traversal_index` sequence (golden) |
| Variant determinism | Same inputs → same winning `variant_id` |
| Route reservation | Second placement cannot block first committed path (regression) |
| Anchor invalidation | No reject spam on consumed footprint anchors |
| L4 shim | `run_layer_04_*` returns `DISABLED`, empty overlay, no probe side effects |
| Stack | `LAYER_04_RIM_BUNDLE_PLACEMENT` not in `completed_layer_slugs` for default runner |
| Reject reasons | Only `RimGreedyRejectReason` enum values |

---

## §10 — Migration checklist (implementation PR sequence)

1. Add contracts + `layer_03_rim_greedy_placement` package (skeleton pass1/pass2).
2. Update `layer_slugs.py`, `stack_runner`, behavior catalog.
3. L4 shim `Layer04DisabledResult`; remove L4 from runners.
4. Deprecate `layer_03_rim_mining_bundles` package (redirect or delete).
5. Tests: golden traversal, reservation regression, stack slug list.
6. Replay segment + post-summary metrics.
7. Mark superseded specs in git when `docs/superpowers` tree is restored on branch.

---

## Appendix — Locked ambiguity resolutions

| # | Decision |
|---|----------|
| 1 | Outer rim order = boundary traversal, not set sort |
| 2 | Invalidate consumed footprint + conflict anchors, not only current anchor |
| 3 | Reserve DPS path on success; equipment hard-blocks reservations in same pass |
| 4 | Pass 2 v0 = read-only score; no repair |

---

**Implementation plan:** [`2026-05-29-layer-03-rim-greedy-placement.md`](../plans/2026-05-29-layer-03-rim-greedy-placement.md)
