# Layer 03 — Virtual Exterior Transport Domain — Design Spec

**Document type:** Solver / Lab contract amendment (L3 geometry + route probe SoT)  
**Status:** **APPROVED (2026-05-28)** — Solver Contract Architect blocking text amendments applied  
**Work classification:** contract change · implementation change  
**Scope:** `layer_03_rim_mining_bundles/` · `layers/shared/route_probe.py` · `layers/contracts/candidates.py` · parent L3 spec §1.2 amendment  
**Supersedes (pool recovery):** [`2026-05-28-layer-03-rim-void-depth-projection-design.md`](2026-05-28-layer-03-rim-void-depth-projection-design.md) (void-depth pre-gate is diagnostic-only at best)  
**Parent:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) (APPROVED — §1.2 A′′ **amended** by this document)

**Architect decision (2026-05-28):** Finite `external_void_cells` MUST NOT be the sole installability set for belt/pipe. M/E remain on `field_cells`. Transport uses a **bounded virtual exterior domain** per candidate route envelope.

---

## §1 — Problem restatement

### 1.1 Symptom (unchanged)

Lab Run on 583-cell map: `seed_projection_attempt_count = 1458`, `route_probe_attempt_count = 0`, `local_geometry_rejected_count = 1458`.

### 1.2 Incorrect root cause (withdrawn)

```text
seed required_void_extent > finite void_depth along ray in external_void_cells
```

This diagnoses a **symptom** of the wrong SoT, not the canonical failure.

### 1.3 Correct root cause (normative)

```text
L3 treated transport_abs_cells ⊆ external_void_cells as installability SoT.
external_void_cells is a finite reconstructed bbox artifact.
Belt/pipe may need virtual exterior coordinates outside that finite set
while still not overlapping asteroid field cells.
Geometry gate therefore rejected feasible exterior routes before probe.
```

### 1.4 PR identity

| This PR | Not this PR |
|---------|-------------|
| Replace transport ⊆ `external_void_cells` with virtual exterior domain | Void-depth pre-gate as primary fix |
| Restore candidate pool on real maps where routes exist | L4/L5/L6 commit semantics |
| New reject reasons aligned to equipment vs transport | Unbounded infinite grid search |
| P0 acceptance: `route_probe_attempt_count > 0` on synthetic virtual-exterior fixture | Using Lab dense/screen coords as input |
| Evidence (optional): production-shaped 583-cell fixture if committed | Void-depth pre-gate as primary fix |

---

## §2 — Equipment vs transport (normative)

### 2.1 Mining equipment (M / E)

```text
miner_cells ⊆ field_cells
extension_cells ⊆ field_cells
mining_occupied_cells ⊆ field_cells
anchor_abs ∈ mining_occupied_cells   (rim anchor on field)
```

**Unchanged.** M/E install only on asteroid field coordinates (map absolute, `ReconstructionCompleteMap.field_cells`).

### 2.2 Transport (belt / pipe)

**Withdrawn rule:**

```text
transport_abs_cells ⊆ external_void_cells   # REMOVED as installability SoT
```

**New rule:**

```text
transport_abs_cells ∩ field_cells = ∅
transport_abs_cells ⊆ exterior_transport_traversable(anchor, route_envelope)
```

Where `exterior_transport_traversable` is a **dynamic bounded** set of map-absolute coordinates:

- Not in `field_cells`
- Inside the route's search envelope (bounded)
- **Exterior-reachable** from the candidate's exterior entry (not interior holes)

**Normative prose (English):**

```text
Miner and extension cells MUST be placed on asteroid field cells.
Belt and pipe cells MUST NOT overlap asteroid field cells and MAY be declared
in virtual exterior coordinates outside the ReconstructionCompleteMap finite
external_void bbox, provided they lie in the candidate's bounded exterior
transport domain and are exterior-reachable from the route entry.
```

**Korean reference:**

```text
M/E는 반드시 소행성 field 안에 설치한다.
벨트/파이프는 소행성 field와 겹치지 않는 한,
기존 bbox 밖 외부 좌표에도 제한적으로 선언할 수 있다.
```

### 2.3 Coordinate model (unchanged from prior architect sign-off)

| Layer | Coordinates |
|-------|-------------|
| Seed catalog | Canonical local-relative offsets |
| Projection | `anchor_abs + rotate(local_offset, output_dir)` → map absolute |
| Gates / probe | Map absolute only |
| Lab UI | Output-only — never solver input |

---

## §3 — Virtual exterior transport domain

### 3.1 `ExteriorTransportDomain` (new DTO)

```python
@dataclass(frozen=True, slots=True)
class ExteriorTransportDomain:
    """Bounded non-field traversable space for one candidate probe context."""

    search_bbox: tuple[int, int, int, int]  # xmin, ymin, xmax, ymax inclusive
    blocked_field_cells: frozenset[Coord]   # field_cells ∩ bbox (and globally enforced)
    placeable_cells: frozenset[Coord]       # exterior-reachable install/search space (§3.6)
```

- **Not** persisted to DB or committed layout.  
- **Not** a second `RouteDomainSnapshotBuilder` — L3 candidate probe only (L6 commit keeps existing snapshot owner per ADR).

### 3.2 Search envelope (bounded “limited infinity”)

For each candidate projection + probe:

```text
envelope_coords = { anchor_abs } ∪ transport_stub_cells ∪ { g.coord for g in route_goals }
search_bbox = expand_bbox(bbox(envelope_coords), EXTERIOR_TRANSPORT_MARGIN_CELLS)
```

`EXTERIOR_TRANSPORT_MARGIN_CELLS` — const (e.g. `8`), tested, documented.

**Forbidden:** unbounded global grid expansion.

### 3.3 Exterior-reachable (interior hole protection)

**Amended 2026-05-28 (weighted routing):** Field cells inside `search_bbox` are walkable at `FIELD_ROUTE_COST` unless in `mining_occupied_cells` (blocked). See [`2026-05-28-layer-03-weighted-transport-routing-design.md`](2026-05-28-layer-03-weighted-transport-routing-design.md).

**Legacy v1 (pre-weighted) graph** — superseded for new L3 route probe by weighted install surface:

```text
node c  iff  c in bbox AND c ∉ field_cells
```

**Weighted v1 (normative for new paths):** `walkable_cells` / install surface derived from `search_bbox`, field ∪ exterior in bbox, minus `mining_occupied_cells` and other blockers. Field is **high-cost** terrain, not a hard blocker.

```text
Interior holes (non-field cells not reachable from transport_entry via walkable graph)
remain unreachable — belt/pipe MUST NOT be placed there without explicit path_coords.
```

**Forbidden:** “any non-field cell in bbox is installable” without bounded search caps; promoting full walkable component into `transport_stub_cells`.

### 3.4 Builder (sole factory)

```python
def build_exterior_transport_domain(
    *,
    complete_map: ReconstructionCompleteMap,
    anchor_abs: Coord,
    transport_stub_cells: frozenset[Coord],
    route_goals: tuple[RouteGoal, ...],
    route_probe_start: Coord,
) -> ExteriorTransportDomain:
    ...
```

Implementation location: `layer_03_rim_mining_bundles/exterior_domain.py` (or `layers/shared/` if L6 later shares — **v1: L3 only**).

### 3.5 Relationship to `external_void_cells`

| Set | Role after this spec |
|-----|----------------------|
| `external_void_cells` | Reconstruction / L2 slot discovery / diagnostics — **not** transport installability SoT |
| `placeable_cells` in domain | L3 route search / installability SoT (not transport connectivity — §3.6) |

Pre-existing void cells ⊆ placeable_cells when inside envelope and same component; **virtual** coords may be ∈ placeable_cells \ external_void_cells.

**Wire/log compatibility (one release, optional):** serialized metrics MAY emit `traversable_cells` as an alias of `placeable_cells`. Solver/runtime Python DTOs MUST use `placeable_cells` only; MUST NOT read `traversable_cells` from in-memory objects.

---

## §3.6 Traversable domain is not transport connectivity

### Installability domain (`placeable_cells`)

```text
placeable_cells = exterior-reachable non-field coordinates inside search_bbox
(interior holes excluded — §3.3)
```

A coordinate ∈ `placeable_cells` means belt/pipe **may be considered for placement** during route search. It does NOT mean adjacent placeable cells are already connected transport.

### Transport network (candidate stage)

```text
proposed_transport_cells = transport_stub_cells ∪ route_probe_result.path_coords
```

- `path_coords` includes **both** `route_probe_start_coord` and `reached goal_coord` (normative).
- Overlap between stubs and path is allowed (intentional merge/share).

**Forbidden:** promoting `domain.placeable_cells` (full component) into `candidate.transport_stub_cells`; using 4-neighbor placeable adjacency alone as proof of transport connectivity.

**Korean reference:** `placeable_cells`는 설치·탐색 후보 공간일 뿐; 연결은 `path_coords`·committed transport·명시 merge만 인정.

---

## §4 — Projection (`project_miner_seed_at_anchor`)

### 4.1 Validation order (revised)

**Amended 2026-05-28 (weighted routing):**

```text
1. Build absolute placements from seed-local offsets (unchanged translator).
2. mining_occupied_cells ⊆ field_cells  → else MINING_CELL_OFF_FIELD
3. transport_stub_cells ∩ mining_occupied_cells = ∅  → else TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT
4. anchor_abs ∈ mining_occupied_cells      → else LOCAL_GEOMETRY_INVALID
5. route_probe_start_coord = transport_entry_coord; MUST NOT require ∈ transport_stub_cells
6. REMOVED (new L3 path): transport_stub_cells ∩ field_cells → TRANSPORT_COLLIDES_WITH_FIELD
7. REMOVED: transport_stub_cells ⊆ external_void_cells
```

**Boundary (normative):** `project_miner_seed_at_anchor` MUST NOT build route domain and MUST NOT accept `route_goals`. It projects seed-local offsets and validates local geometry (M/E on field, transport vs M/E only). Exterior/field-weighted reachability is validated **after** projection in `expand.py` via weighted route domain + `weighted_route_probe`.

Cross-link: [`2026-05-28-layer-03-weighted-transport-routing-design.md`](2026-05-28-layer-03-weighted-transport-routing-design.md).

### 4.2 Reject reason changes

Add to `CandidateRejectReason`:

```python
TRANSPORT_COLLIDES_WITH_FIELD = "transport_collides_with_field"
EXTERIOR_ENTRY_NOT_REACHABLE = "exterior_entry_not_reachable"
EXTERIOR_CONNECTOR_UNREACHABLE = "exterior_connector_unreachable"  # probe-phase
```

| Reason | When |
|--------|------|
| `TRANSPORT_COLLIDES_WITH_FIELD` | Any transport cell ∈ `field_cells` |
| `EXTERIOR_ENTRY_NOT_REACHABLE` | `route_probe_start` not in traversable component |
| `TRANSPORT_STUB_NOT_IN_VOID` | **Decision A:** retained for historical wire compatibility; **MUST NOT** be emitted by new virtual-exterior paths; Lab **MUST NOT** remap old metrics to `TRANSPORT_COLLIDES_WITH_FIELD` (distinct semantics) |
| `INSUFFICIENT_VOID_DEPTH` | Optional diagnostic only if void-depth observability PR lands separately |

---

## §5 — Route probe (`immediate_route_probe`)

### 5.1 Traversable SoT change

**Before:**

```python
immediate_route_probe(..., traversable_void=complete_map.external_void_cells)
```

**After:**

```python
domain = build_exterior_transport_domain(...)
immediate_route_probe(..., placeable_cells=domain.placeable_cells)
```

Goals must be ∈ `placeable_cells` to succeed; BFS bounded by `LAYER03_ROUTE_PROBE_MAX_STEPS` (unchanged).

### 5.3 Probe path semantics

```text
BFS walks placeable_cells (search space only).
On success, RouteProbeResult.path_coords is a simple shortest path.
path_coords includes route_probe_start and reached goal_coord.
path_coords MUST NOT be replaced by the full placeable component.
```

`RouteProbeResult.proposed_transport_cells(stub_cells=...)` returns `stub_cells ∪ path_coords` only — not `placeable_cells`.

### 5.2 Failure mapping

| Condition | `reject_reason` |
|-----------|-----------------|
| Start ∉ traversable | `EXTERIOR_ENTRY_NOT_REACHABLE` |
| No goal reachable | `EXTERIOR_CONNECTOR_UNREACHABLE` or `ROUTE_PROBE_FAILED` (pick one; normative: `EXTERIOR_CONNECTOR_UNREACHABLE`) |

---

## §6 — L3 enumeration flow (revised)

**Output direction naming:** L3 uses **exterior/outward** direction from rim field toward exterior space. Implement as `select_exterior_output_dir` (rename from `select_fieldward_output_dir`). Do not reuse L2 connector “fieldward-facing” terminology in L3 API names unless explicitly documented as a conversion layer.

```text
FOR anchor IN outer_rim:
  output_dir ← select_exterior_output_dir(...)
  IF output_dir is None:
    diagnostic NO_EXTERIOR_VOID_NEIGHBOR
    CONTINUE

  FOR seed IN catalog:
    projection ← project_miner_seed_at_anchor(...)   # projection + local geometry ONLY
    IF projection.candidate is None:
      diagnostic SKIPPED_GEOMETRY + reject_reason
      CONTINUE

    domain ← build_exterior_transport_domain(...)   # expand/probe ONLY
    IF NOT candidate.transport_stub_cells ⊆ domain.placeable_cells:
      diagnostic SKIPPED_GEOMETRY + EXTERIOR_ENTRY_NOT_REACHABLE
      CONTINUE
    IF candidate.route_probe_start_coord ∉ domain.placeable_cells:
      diagnostic SKIPPED_GEOMETRY + EXTERIOR_ENTRY_NOT_REACHABLE
      CONTINUE

    probed ← immediate_route_probe(..., placeable_cells=domain.placeable_cells)
    # MUST NOT mutate candidate.transport_stub_cells with placeable or path_coords
    ...
```

Void-depth pre-gate (optional observability PR) MAY remain as early short-circuit but MUST NOT block implementation of this spec.

---

## §7 — Testing (normative)

### 7.1 P0 — Contract tests

| ID | Test | Acceptance |
|----|------|------------|
| T1 | M/E off field | `MINING_CELL_OFF_FIELD` |
| T2 | Transport overlaps field | `TRANSPORT_COLLIDES_WITH_FIELD` |
| T3 | Transport beyond finite `external_void_cells` | Projection + probe **allowed** when no field collision and connector reachable |
| T4 | Interior hole | Non-field cell inside asteroid hole — **not** traversable; transport into hole → reject |
| T5 | Golden 5×5 | Existing L3 success tests remain green |
| T6 | Synthetic virtual-exterior fixture | `route_probe_attempt_count > 0` **required** (P0 hard gate) |
| T7 | Production-shaped 583-cell fixture (optional) | `route_probe_attempt_count > 0` if fixture exists in repo — evidence only |

### 7.2 Withdrawn as canonical tests

```text
void depth 1 + seed extent 2 → INSUFFICIENT_VOID_DEPTH
```

May remain as optional diagnostic test only.

### 7.3 P0 acceptance (this PR)

```text
P0 hard gate:
  synthetic virtual-exterior fixture → route_probe_attempt_count > 0

Evidence / optional:
  production-shaped 583-cell fixture → route_probe_attempt_count > 0 if fixture committed
```

---

## §8 — Metrics / observability

Keep / add:

- `reject_reason_counts` (histogram over **all** `diagnostic_rejected_candidates`, geometry + route-probe stages; sum need not equal `local_geometry_rejected_count`)
- `projection_call_count`
- Optional: `virtual_transport_cell_count` — transport cells ∈ traversable \ external_void_cells (output-only)

Lab L3 highlights: top reject reasons; do not require pool > 0 for unrelated observability-only PRs.

---

## §9 — Parent spec amendment

Patch [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md) §1.2:

Replace:

```text
transport_stub_cells ⊆ external_void_cells
```

With §2.2 of this document (equipment vs transport split).

---

## §10 — Implementation plan status

| Artifact | Status |
|----------|--------|
| [`2026-05-28-layer-03-rim-void-depth-projection.md`](../plans/2026-05-28-layer-03-rim-void-depth-projection.md) | **BLOCKED** until this spec APPROVED; optional observability subset may be cherry-picked later |
| New plan (after approval) | `2026-05-28-layer-03-virtual-exterior-transport-domain.md` via `writing-plans` |

---

## §11 — Spec self-review

| Check | Result |
|-------|--------|
| Interior holes | §3.3 explicit BFS component rule |
| Infinite grid | §3.2 bounded bbox + margin |
| L6 snapshot ownership | L3-only domain; no commit snapshot patch in v1 |
| Contradiction with void-depth spec | Void-depth spec superseded for recovery |
| Lab coords forbidden | §2.3 |

---

## §12 — Approval record

```text
Status: APPROVED (2026-05-28)

Decision:
- finite external_void_cells is no longer transport installability SoT
- M/E remain constrained to field_cells
- belt/pipe may occupy bounded virtual exterior coordinates
- project_miner_seed_at_anchor remains projection/local-geometry only
- ExteriorTransportDomain is built after projection and used by route probe
- TRANSPORT_STUB_NOT_IN_VOID is deprecated-retained, never emitted on new paths
- select_exterior_output_dir replaces select_fieldward_output_dir in L3 API

2026-05-28 — Amendment (transport connectivity split):
- placeable_cells replaces traversable_cells on Python DTO (wire alias optional one release)
- placeable_cells = install/search space; path_coords = explicit route; no full-component promotion
- path_coords includes start and goal; proposed_transport_cells = stubs ∪ path_coords
- reject_reason_counts = all L3 diagnostic rejects
```

Implementation plan: [`2026-05-28-layer-03-virtual-exterior-transport-domain.md`](../plans/2026-05-28-layer-03-virtual-exterior-transport-domain.md)
