# Layer 03 — Weighted Transport Routing with Mining Occupancy Priority — Design Spec

**Document type:** Solver / Lab contract amendment (L3 projection + route probe)  
**Status:** **APPROVED WITH BLOCKING AMENDMENTS (2026-05-28)** — Solver Contract Architect  
**Work classification:** contract change · implementation change  
**Scope:** `project.py` · `exterior_domain.py` · `route_probe.py` · `expand.py` · `candidates.py` · observability  
**Parent:** [`2026-05-28-layer-03-rim-mining-bundles-design.md`](2026-05-28-layer-03-rim-mining-bundles-design.md)  
**Amends (supersedes in part):**
- [`2026-05-28-layer-03-virtual-exterior-transport-domain-design.md`](2026-05-28-layer-03-virtual-exterior-transport-domain-design.md) §3.3, §4.1
- [`2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md`](2026-05-28-layer-03-footprint-aware-exterior-direction-enumeration-design.md) (projection gates only)

**Implementation plan:** [`2026-05-28-layer-03-weighted-transport-routing.md`](../plans/2026-05-28-layer-03-weighted-transport-routing.md)

**Does not change:** R2-lite direction enumeration · M/E ⊆ field_cells · `proposed_transport_cells = stubs ∪ path_coords` · L4/L5 semantics

**Korean title (reference):** L3 가중 경로 탐색 — field는 고비용 허용, M/E occupied는 hard blocker

---

## §1 — Problem

After R2-lite, 583-cell Lab still shows `route_probe_attempt_count = 0` with:

```text
mining_cell_off_field: 1225
local_geometry_invalid.probe_start_not_transport: 579
transport_collides_with_field: 140
```

**Withdrawn interpretation:** belt/pipe must never touch `field_cells`.

**Normative correction:**

```text
Field collision is not transport collision.
Mining equipment collision is transport collision.
Field transport is allowed but expensive.
Route probe plans a new belt/pipe path; it does not require pre-installed belt at the entry cell.
```

---

## §2 — Hard invariants

### 2.1 M/E on field

```text
mining_occupied_cells = miner_cells ∪ extension_cells
mining_occupied_cells ⊆ field_cells
```

Else: `MINING_CELL_OFF_FIELD`.

### 2.2 Transport vs M/E

```text
transport_stub_cells ∩ mining_occupied_cells = ∅
path_coords ∩ mining_occupied_cells = ∅   (probe path must not cross M/E)
```

Else: `TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT` (new).

### 2.3 Withdrawn (new L3 paths)

```text
transport_stub_cells ∩ field_cells = ∅  → TRANSPORT_COLLIDES_WITH_FIELD
```

`TRANSPORT_COLLIDES_WITH_FIELD` remains in enum for wire compatibility; **MUST NOT** be emitted from new L3 projection/expand paths or appear in Lab histograms from the new path.

### 2.4 Transport entry (replaces “probe start on stub”)

```text
route_probe_start_coord  (wire name unchanged) = transport_entry_coord
```

Meaning: first coordinate where belt/pipe routing may begin from miner output direction.

**Required before probe:**

```text
transport_entry_coord ∉ mining_occupied_cells
domain.step_cost(transport_entry_coord) is not None   (coord is on bounded install surface)
```

**Not required:**

```text
transport_entry_coord ∈ transport_stub_cells
```

**Reachability:** `weighted_route_probe` (Dijkstra) is the **sole authority** for start→goal reachability in P0. No separate BFS “reachable component” gate in `expand.py`.

**Korean reference:**

```text
asteroid field는 belt/pipe 금지 영역이 아니다.
belt/pipe는 field 위에도 설치 가능하다.
다만 M/E가 field 사용 우선권을 가지므로,
M/E occupied cell은 transport hard blocker이고,
field 위 transport는 높은 비용/낮은 우선순위로 처리한다.
```

---

## §3 — Transport entry derivation (v1)

Canonical E miner at `anchor_coord` (map-absolute M):

```python
steps = steps_from_canonical_e(output_dir)
offset = rotate_offset(CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET, steps)  # (1, 0) in canonical E
transport_entry_coord = anchor_coord + offset
```

If `transport_entry_coord ∈ mining_occupied_cells` → `TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT`.

If a seed `transport_stub_cells` contains `transport_entry_coord`, that cell may be reused; routing still may extend via `path_coords`.

**Removed:** `CANONICAL_ROUTE_PROBE_START_OFFSET (2,0)` as mandatory pre-installed stub gate.

### 3.1 v1 caveat (normative)

```text
v1 transport_entry_coord is derived from CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET only.
It is the first route-search entry coordinate, not necessarily an existing seed transport stub.
Future seeds with alternate output ports require explicit seed output-port metadata (out of v1 scope).
```

---

## §4 — Weighted route domain

### 4.1 Walkable / install surface (bounded — not “whole bbox blindly”)

**Forbidden mental model:**

```text
walkable_cells = cells_in_bbox(search_bbox) - mining_occupied_cells   # as sole documentation
```

That makes every bbox coordinate appear equally routable and allows overly wide detours unless hard search caps apply.

**Normative v1 definition:**

```text
candidate_cells = cells_in_bbox(search_bbox)

install_surface_cells =
  (complete_map.field_cells ∩ candidate_cells)           # field terrain in envelope
  ∪ (candidate_cells \ complete_map.field_cells)         # exterior / void / virtual in envelope

walkable_cells =
  install_surface_cells
  - mining_occupied_cells
  - incompatible_transport_cells
  - explicit_blocked_cells
```

| Set | v1 |
|-----|-----|
| `incompatible_transport_cells` | `∅` (reserved; v1 has no pre-existing exterior network) |
| `explicit_blocked_cells` | `∅` (reserved; future interior-hole / policy blocks) |

**Normative (English):**

```text
walkable_cells is a bounded search surface for route installation/search,
derived from search_bbox and blocked-occupancy policy.
It MUST NOT be promoted into candidate.transport_stub_cells or proposed_transport_cells.
Dijkstra path_coords (stubs ∪ path) are the only transport network evidence at candidate stage.
```

**Hard bounds (P0 — required):**

| Constant | Value | Limits |
|----------|-------|--------|
| `EXTERIOR_TRANSPORT_MARGIN_CELLS` | `8` (existing) | `search_bbox` extent |
| `LAYER03_ROUTE_PROBE_MAX_PATH_CELLS` | `64` | returned `len(path_coords)` |
| `LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES` | `512` | Dijkstra pop/expansion count |

`LAYER03_ROUTE_PROBE_MAX_STEPS` (legacy name) **MAY** alias to `MAX_PATH_CELLS` in code for one release; new code MUST use the split constants above.

### 4.2 Cost model v1

| Cell class | Step cost |
|------------|-----------|
| `coord ∈ field_cells \ mining_occupied_cells` (and ∈ `walkable_cells`) | `FIELD_ROUTE_COST` (25) |
| Other `coord ∈ walkable_cells` | `EXTERIOR_ROUTE_COST` (1) |
| `coord ∉ walkable_cells` | blocked (`step_cost` returns `None`) |

Constants: `django_apps/asteroid_lab/layers/contracts/weighted_transport_route_domain.py` and `route_probe.py`.

### 4.3 Search algorithm

**Dijkstra** (or A*) over 4-neighbors in `walkable_cells` with `step_cost`.

**Caps (both enforced):**

```text
len(path_coords) <= LAYER03_ROUTE_PROBE_MAX_PATH_CELLS
expanded_node_count <= LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES
```

Among reachable goals, choose minimum `(total_route_cost, goal.priority, len(path_coords), goal.goal_id)`.

**Forbidden:** separate `reachable_walkable_from_start` BFS in `expand.py` as a second reachability authority (P0).

### 4.4 Transport network (unchanged)

```text
proposed_transport_cells = transport_stub_cells ∪ route_probe_result.path_coords
```

Forbidden: `candidate.transport_stub_cells = domain.walkable_cells` or full-component promotion.

---

## §5 — `RouteProbeResult` extension

| Field | Type | Meaning |
|-------|------|---------|
| `route_cost` | `int` | Sum of per-step costs along `path_coords` (define: sum of `step_cost` for each cell entered, excluding blocked) |
| `field_route_cell_count` | `int` | Count of cells in `path_coords` that ∈ `field_cells` (entry may count if on field) |

Retain: `path_coords[0] == candidate.route_probe_start_coord`, `path_coords[-1] == goal_coord` when succeeded.

---

## §6 — Reject reasons

Add:

```python
TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT = "transport_collides_with_mining_equipment"
```

Deprecate emit from new paths:

```python
TRANSPORT_COLLIDES_WITH_FIELD  # MUST NOT be emitted by project.py / expand.py (P0 regression test)
```

Remove histogram subreason:

```text
local_geometry_invalid.probe_start_not_transport
```

---

## §7 — Testing (normative)

### P0 (synthetic)

- Transport on field allowed; **`TRANSPORT_COLLIDES_WITH_FIELD` not emitted** from `project_miner_seed_at_anchor` (dedicated test).
- Transport overlapping M/E → `TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT`.
- Entry not in `transport_stub_cells`; `domain.step_cost(entry)` valid → `route_probe_attempt_count > 0`.
- Exterior route preferred over field when both exist (lower `route_cost`).
- Field-only fallback when exterior-only path impossible.
- `probe_start_not_transport` not in histogram.
- Expand histogram: `transport_collides_with_field` count == 0 on new-path fixtures.

### P1 (evidence)

- 583-shaped or captured fixture: `route_probe_attempt_count > 0`; `probe_start_not_transport` → 0; `transport_collides_with_field` not emitted.

---

## §8 — Approval record

```text
Status: APPROVED WITH BLOCKING AMENDMENTS (2026-05-28)

Architect decision:
  Direction approved: field = high-cost transport; M/E occupied = hard blocker;
  transport entry ≠ pre-installed stub; weighted Dijkstra plans path_coords.

Blocking amendments incorporated in this revision:
  [x] walkable domain semantics bounded + blocker policy (§4.1)
  [x] reachable_walkable_from_start removed from P0; Dijkstra sole reachability authority (§2.4, §4.3)
  [x] transport_entry_coord v1 fixed-output caveat (§3.1)
  [x] TRANSPORT_COLLIDES_WITH_FIELD not-emitted regression test (§7)
  [x] Dijkstra MAX_PATH_CELLS vs MAX_EXPANDED_NODES split (§4.1, §4.3)

Implementation authorized per plan:
  docs/superpowers/plans/2026-05-28-layer-03-weighted-transport-routing.md
```
