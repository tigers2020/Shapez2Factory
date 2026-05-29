# Layer 04 — Rim Bundle Provisional Placement + Replay Materialization — Design Spec

**Document type:** Solver / Lab contract (Layer 4 selection + ephemeral overlay)  
**Status:** **APPROVED (2026-05-28)** — Option B (Ephemeral `ProvisionalLayoutOverlay`)  
**Work classification:** contract change · implementation change  
**Scope:** `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/` · `layers/contracts/` · `stack_runner` L3→L4→L5 wiring · layer renumber (inner fill → L5, commit → L6)  
**Extends:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) · [`2026-05-27-asteroid-lab-algorithm-layer-stack-design.md`](2026-05-27-asteroid-lab-algorithm-layer-stack-design.md)

**Implementation plan:** [`2026-05-28-layer-04-rim-bundle-placement-pr3c.md`](../plans/2026-05-28-layer-04-rim-bundle-placement-pr3c.md)

**Korean title (reference):** L4 rim 번들 잠정 배치(overlay) + replay 관측 — CompleteMap 불변

---

## §1 — Purpose and boundaries

### 1.1 Identity

| Item | Contract |
|------|----------|
| Slug | `layer_04_rim_bundle_placement` |
| Purpose | Consume L3 `normal_candidates`; **deterministic physical non-overlap selection**; materialize `PROVISIONAL_PLACED` placements + `ProvisionalLayoutOverlay`; **runtime replay frames via central assembler** (not layer package) |
| Output | `Layer04RimPlacementResult` (includes `provisional_overlay`) |
| Dense coverage meaning | **Provisional stack occupancy** — not committed layout |

### 1.2 Stack position (normative)

```text
L1 ReconstructionCompleteMap (immutable canonical)
L2 ExteriorConnectionPlan
L3 RimBundleCandidateSet
L4 Layer04RimPlacementResult + ProvisionalLayoutOverlay   ← this spec
L5 Inner pattern fill (complete_map + overlay + rim plan)
L6 Commit / validate
```

**Deferred:** prior stack table `layer_06_floor2_space_link` becomes **L7** when implemented.

### 1.3 Option B — Ephemeral overlay (approved)

```text
Layer 04 MUST NOT mutate ReconstructionCompleteMap or committed layout.
Layer 04 MUST build ProvisionalLayoutOverlay as stack-internal derived state.
L5/L6 consume: complete_map + provisional_overlay + placement_result (+ exterior_plan).
Replay frames are observability only — MUST NOT be read as algorithm input.
```

### 1.4 Forbidden (normative)

```text
MUST NOT mutate ReconstructionCompleteMap
MUST NOT write committed layout
MUST NOT perform route commit
MUST NOT emit ROUTED_CONFIRMED or CONFIRMED placement in L4
MUST NOT re-run route probe or change L3 candidate expectations
MUST NOT equivalence-dedupe (L3 already deduped)
MUST NOT modify L2 ExteriorConnectionPlan
MUST NOT use replay / NDJSON / solver_summary as algorithm input
```

---

## §2 — Layer table amendment

| Layer | Slug | Package |
|-------|------|---------|
| 3 | `layer_03_rim_mining_bundles` | unchanged |
| **4** | **`layer_04_rim_bundle_placement`** | **new** |
| 5 | `layer_05_inner_pattern_fill` | renamed from `layer_04_inner_pattern_fill` |
| 6 | `layer_06_commit_validate` | renamed from `layer_05_commit_validate` |

**Budget:** L2–L6 share the existing **60s cumulative** wall clock owned by `stack_runner` (`LayerBudgetContext`).

---

## §3 — DTOs and enums

### 3.1 Shared — `PlacementCommitState`

Path: `layers/contracts/placement_state.py`

```python
class PlacementCommitState(StrEnum):
    PROVISIONAL_PLACED = "PROVISIONAL_PLACED"
    ROUTED_CONFIRMED = "ROUTED_CONFIRMED"
    QUARANTINED_UNROUTED = "QUARANTINED_UNROUTED"
    ROLLED_BACK = "ROLLED_BACK"
```

**L4 may only emit** `PROVISIONAL_PLACED`.

### 3.2 Shared — `ProvisionalLayoutOverlay`

Path: `layers/contracts/provisional_overlay.py`

```python
@dataclass(frozen=True, slots=True)
class ProvisionalPlacedCell:
    coord: Coord
    candidate_id: str
    placement_id: str
    role: BundleCellRole
    transport_kind: TransportKind
    placement_state: PlacementCommitState  # PROVISIONAL_PLACED in L4

@dataclass(frozen=True, slots=True)
class ProvisionalLayoutOverlay:
    occupied_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    transport_stub_cells: frozenset[Coord]
    by_cell: Mapping[Coord, ProvisionalPlacedCell]
    source_layer: str = "layer_04_rim_bundle_placement"
```

`by_cell` keys MUST equal `occupied_cells`. Aggregates MUST be consistent with `by_cell` role partitions.

**Immutability:** `__post_init__` MUST wrap `by_cell` with `types.MappingProxyType` so callers cannot mutate the internal dict through a frozen dataclass shell.

### 3.3 Layer 04 — placement result

Path: `layers/contracts/rim_placement.py`

```python
class RimPlacementRejectReason(StrEnum):
    PHYSICAL_OVERLAP = "PHYSICAL_OVERLAP"
    BUDGET_INTERRUPTED = "BUDGET_INTERRUPTED"
    NON_SUCCEEDED_PROBE = "NON_SUCCEEDED_PROBE"  # defensive; normal pool is SUCCEEDED-only

@dataclass(frozen=True, slots=True)
class RimBundlePlacement:
    candidate_id: str
    placement_id: str
    equivalence_key: str
    gene_key: str
    anchor_coord: Coord
    transport_kind: TransportKind
    resource_kind: ResourceKind
    occupied_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    output_stub_cells: frozenset[Coord]
    route_probe_goal_cells: frozenset[Coord]
    placement_state: PlacementCommitState
    intrinsic_priority_rank: int

@dataclass(frozen=True, slots=True)
class RimPlacementRejection:
    candidate_id: str
    equivalence_key: str
    reason: RimPlacementRejectReason
    conflicting_candidate_id: str | None = None
    conflicting_cells: frozenset[Coord] = frozenset()

@dataclass(frozen=True, slots=True)
class Layer04RimPlacementResult:
    selected_placements: tuple[RimBundlePlacement, ...]
    rejected_candidates: tuple[RimPlacementRejection, ...]
    selected_count: int
    rejected_overlap_count: int
    rejected_budget_count: int
    provisional_overlay: ProvisionalLayoutOverlay
    replay_frames: tuple[ReplayFrameAppendDTO, ...]
```

**Construction:** Production code MUST build results via `build_layer04_rim_placement_result(...)` only (validates `selected_count`, rejection counts, overlay). Direct `Layer04RimPlacementResult(...)` is for tests and raises on invariant violation at construction time.

**Cell derivation from L3 `BundleCandidate.placements`:**

| `BundleCellRole` | Target field |
|------------------|--------------|
| `MINER` | `extractor_cells` |
| `EXTENSION` | `extension_cells` |
| `TRANSPORT_STUB` | `output_stub_cells` (subset) + overlay `transport_stub_cells` |

`occupied_cells = mining_occupied_cells | transport_stub_cells` (same as L3 footprint union).

`route_probe_goal_cells = frozenset({goal_coord})` when `route_probe_result.goal_coord` is set; else `frozenset()`.

`placement_id = f"{candidate_id}:prov"` (deterministic).

### 3.4 Selection (normative)

> **Superseded (2026-05-30):** Sort key and overlap rejection metadata replaced by [`2026-05-30-outer-rim-direction-arbitration-design.md`](2026-05-30-outer-rim-direction-arbitration-design.md) §3–§4 (mining-first greedy; `effective_mining_gain`).

**Sort key (ascending) — historical:**

1. `intrinsic_priority_rank`
2. `anchor_coord` stable order: `(y, x)` — same as `sorted_outer_rim_anchors`
3. `equivalence_key`
4. `candidate_id`

**Accept when:**

```text
route_probe_status == SUCCEEDED   # normal pool invariant
occupied_cells ∩ selected_occupied == ∅
budget_ctx.remaining_budget_ms() > 0 at decision time
```

**Reject overlap:** lower-priority candidate (later in sort order) gets `PHYSICAL_OVERLAP` with `conflicting_candidate_id` of the winner.

**No equivalence dedupe** in L4.

**L2 hold:** when `exterior_plan is None` OR `len(normal_candidates)==0`, return empty selections, empty overlay (`ProvisionalLayoutOverlay.empty()`), `selected_count == 0`.

---

## §4 — Replay contract

**Authority (2026-05-28):** Layer 04 MUST NOT build `solver_runtime_replay_frames` or import `ReplayTimelineFrame`. Frame projection lives in `django_apps/asteroid_lab/replay/layer04_segment.py`; ordering and JSON output in `replay/solver_runtime_assembler.py`. See [`2026-05-28-central-solver-runtime-replay-assembler-design.md`](2026-05-28-central-solver-runtime-replay-assembler-design.md).

`run_layer_04_rim_bundle_placement` returns `replay_frames=()` (deprecated field; removal v1.1). Assembler reads `selected_placements` / `rejected_candidates` only.

### 4.1 Event types

Register in `django_apps/asteroid_lab/replay/event_types.py` and `SNAPSHOT_EVENT_TYPES`.

**Registry semantics:** In this repo, `SNAPSHOT_EVENT_TYPES` is the **allowlist of all `event_type` strings permitted in replay frames** (see `event_types.py` module doc: persisted in `ReplayFrame.frame_payload`). It is **not** limited to full-map snapshot milestones. All four Layer04 kinds below MUST be registered so `assert_registered_event_type` passes for overlap-rejection diagnostic frames as well as begin/complete frames.

```text
layer04_rim_placement_begin
layer04_rim_candidate_selected
layer04_rim_candidate_rejected_overlap
layer04_rim_placement_complete
```

### 4.2 Frame metadata (minimum)

```json
{
  "layer": "layer_04_rim_bundle_placement",
  "placement_state": "PROVISIONAL_PLACED",
  "candidate_id": "...",
  "equivalence_key": "...",
  "gene_key": "...",
  "transport_kind": "shape_belt",
  "anchor_coord": {"x": 8, "y": 4},
  "occupied_cell_count": 5
}
```

**UI color contract (documentation only in PR-3c):** provisional > candidate highlight > confirmed (L6).

### 4.3 Separation

```text
ReplayTimelineFrame (wire via solver_runtime_assembler) = output artifact (observability)
ReplayFrameAppendDTO on Layer04RimPlacementResult = deprecated v1 stub (always empty in production)
ProvisionalLayoutOverlay = stack runner wire between L4 → L5
```

Segment builder `build_layer04_runtime_segment_frames` receives `base_map_view` from the assembler only — MUST NOT scan prior frame lists.

---

## §5 — `stack_runner` wiring

Rename runner API: `run_layers_02_to_06` (update all call sites).

```text
L2 → exterior_plan
L3 → candidate_set (needs exterior_plan)
L4 → placement_result + overlay (needs complete_map, exterior_plan, candidate_set)
L5 → stub accepts rim_placement_result + provisional_overlay (signature only in PR-3c)
L6 → stub (renamed package)
```

On budget exhaustion **before** a layer starts: fail-closed (existing behavior); layers after the failed slot MUST NOT run.

---

## §6 — Non-goals (PR-3c)

```text
L5 inner fill generator implementation
L6 commit / route commit / validation
UI theme implementation for provisional colors
Persisting replay frames to DB from stack_runner (frames returned in DTO only)
```

---

## §7 — Related documents

| Doc | Relationship |
|-----|----------------|
| [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) | L3 overlap pool; L4 selection owner |
| [`2026-05-27-asteroid-lab-algorithm-layer-stack-design.md`](2026-05-27-asteroid-lab-algorithm-layer-stack-design.md) | Parent stack — table patch in follow-up doc PR |

---

## Approval record

```text
2026-05-28 — APPROVED (Layer Stack Contract Architect)
  Option B: ProvisionalLayoutOverlay; CompleteMap immutable
  Layer renumber: inner fill → L5, commit → L6
  RimPlacementRejectReason enum (no free-form rejection strings)
```
