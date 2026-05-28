# Layer 02 — Exterior Connector Placement — Design Spec

**Document type:** Solver / Lab contract (Layer 2 placement + observability)  
**Status:** **APPROVED (2026-05-28)** — Asteroid Lab Solver Contract Reviewer  
**Work classification:** contract change · implementation change (follow-up) · UI change (Lab replay)  
**Scope:** `django_apps/asteroid_lab/layers/layer_02_exterior_transport/` · Lab timeline enrichment · `asteroid_miner_layout_lab.js`  
**Extends:** [`2026-05-27-asteroid-lab-algorithm-layer-stack-design.md`](2026-05-27-asteroid-lab-algorithm-layer-stack-design.md) (Layer-2 `ExteriorConnectionPlan` / `ExteriorConnector`)  
**Out of scope:** Layer 3+ route probe · committed placement mutation (Layer 5) · `optimization/` resurrection

**Korean title (reference):** Layer 02 외부 커넥터(Space Belt / Space Pipe) 배치 — void deep slots + edge-weighted spacing + fieldward facing

---

## Approval record (2026-05-28)

```text
§1–§4 APPROVED (Contract Reviewer).

Amendments applied in-doc (2026-05-28):
- `choose_even_slots` uses explicit half-up integer rounding `(numer + denom // 2) // denom - 1` (not Python `round()`).
- `layout_t` is base `SpaceBelt_Forward` / `SpacePipe_Forward`; facing via `rotation` only.

Final rules:
  VOID_DEEP_SLOTS_V1
  + EDGE_WEIGHTED_EVEN_SPACING_V1
  + FIELDWARD_FACING_V1

Rotation convention R0_E_CW:
  R=0 East, R=1 South, R=2 West, R=3 North (clockwise).

Fieldward rotation by edge bucket:
  N→1, E→2, S→3, W→0

Deliverable B:
  L2 planned_connectors is SoT;
  Lab white marker + replay sprite at void_coord.
```

---

## Normative boundary

```text
Exterior connector placement is Layer-2 solver output derived only from
ReconstructionCompleteMap + throughput target + EVTC resolver.

It MUST NOT read replay metrics (terrain_rim_highlight, prior overlay),
overlay_cells, solver_summary artifacts, or optimization/RTTP packages as input.

Lab metrics (exterior_connector_plan) and map_view overlay enrichment are
output-only observability — never solver, topology, candidate, route, commit,
or validation input for any layer.
```

`terrain_rim_highlight` geometry may share helpers with rim highlight DTO builders, but **must not** consume replay wire as L2 input.

---

## Contract summary

```text
ConnectorPlacementRule =
  VOID_DEEP_SLOTS_V1
  + EDGE_WEIGHTED_EVEN_SPACING_V1
  + FIELDWARD_FACING_V1
```

```text
Rotation convention (building / connector sprite facing — NOT shape rotation):
  R=0 → East
  R=1 → South
  R=2 → West
  R=3 → North
  R increases clockwise (R0_E_CW).
```

Shapez 2 **shape** rotation (e.g. Rotator) is unrelated. `ExteriorConnector.rotation` is **connector sprite / building facing** only.

```text
Connector sprite facing: FIELDWARD_FACING_V1
  Connector is placed in external_void.
  Sprite faces back toward the asteroid field / outer rim.
```

---

## §1 — Slot catalog: `VOID_DEEP_SLOTS_V1`

### 1.1 Outer-rim source of truth

The game outer rim is the contact boundary between mineable field and void.

```text
outer_rim_field = field_rim_cells(complete_map.field_cells)
```

Definition:

```text
f ∈ outer_rim_field  ⇔
  f ∈ field_cells
  ∧ ∃ 4-neighbor n of f such that n ∉ field_cells
```

`outer_rim_field` seeds void-depth BFS only. Connector anchors are **not** field cells.

### 1.2 External void anchor

```python
@dataclass(frozen=True, slots=True)
class ExteriorConnector:
    connector_id: str          # "ext_conn_00", deterministic
    void_coord: Coord          # anchor; ∈ external_void_cells
    edge: CardinalEdge         # north | east | south | west
    layout_t: str              # SpaceBelt_* | SpacePipe_*
    rotation: int              # R0_E_CW — connector sprite facing
    capacity_per_min: Decimal  # EVTC per-connector cap
    coords: tuple[Coord, ...]  # v1: (void_coord,) only
```

Normative coordinate rule:

```text
void_coord ∈ external_void_cells
void_depth(void_coord) ≥ 5
```

**Amendment to layer-stack minimum DTO:** replace normative reliance on unnamed `coords` alone; `void_coord` is the anchor; `coords` mirrors v1 singleton for wire compatibility.

### 1.3 Void depth

`void_depth` is assigned by deterministic multi-source 4-neighbor BFS over `external_void_cells`.

```text
void_depth(v) = BFS distance from v to the seed frontier,
  where seeds are rim-adjacent external_void cells (depth 1).
```

Depth semantics:

| Depth | Meaning | Eligible |
|------:|---------|----------|
| `1` | First void ring touching field rim | No |
| `2–4` | Shallow exterior void | No |
| `5` | First allowed connector depth | Yes |
| `>5` | Deep exterior void | Yes |

```text
eligible_void(v) ⇔
  v ∈ external_void_cells
  ∧ void_depth(v) ≥ 5
```

### 1.4 BFS seed construction

For every `f ∈ outer_rim_field`, inspect 4-neighbors `n`:

```text
If n ∈ external_void_cells:
  enqueue seed n with:
    void_depth = 1
    source_field = f
    source_edge = direction from f to n
```

| `source_edge` | Meaning |
|---------------|---------|
| `N` | void seed is north of the field rim cell |
| `E` | void seed is east of the field rim cell |
| `S` | void seed is south of the field rim cell |
| `W` | void seed is west of the field rim cell |

BFS expansion:

```text
- Expand only through external_void_cells.
- First visit wins (do not decrease void_depth).
- Ties resolved deterministically.
```

Tie-break (normative):

```text
1. edge order: N, E, S, W
2. source_field coordinate lexicographic (x, then y)
3. neighbor expansion order: N, E, S, W
```

Edge bucket for deep void slots inherits BFS source edge:

```text
edge(v) = bfs_source_edge[v]
```

**Forbidden:** global `nearest_field(v) = argmin manhattan(v, f)` for edge bucketing (concave rims misbucket; non-normative).

### 1.5 Candidate slots by edge

```python
candidate_slots_by_edge[edge] = sorted(
    [v for v in eligible_void if bfs_source_edge[v] == edge],
    key=edge_sort_key[edge],
)
```

| Edge | Sort key |
|------|----------|
| `N` | `x` ascending |
| `E` | `y` ascending |
| `S` | `x` descending |
| `W` | `y` descending |

```text
edge_len = len(candidate_slots_by_edge[edge])
```

`edge_len` is the count of usable deep void slots — **not** bbox width/height and not `outer_outline_loops` arc length.

### 1.6 Failure condition

```text
sum(edge_len for all edges) < required_connectors
  → unmet_reason = ExteriorConnectionShortfallReason.NO_FEASIBLE_CONNECTOR_SITES
```

A shallow side may produce `edge_len = 0`. Distribution allocates only to edges with feasible slots.

---

## §2 — Placement rule: `EDGE_WEIGHTED_EVEN_SPACING_V1`

### 2.1 Required connector count

From EVTC resolver only (no literals in layer code):

```python
required_connectors = ceil(planning_target_per_min / per_connector_capacity_per_min)
```

Shape example (observability; values from DB):

```python
connector_capacity = line_throughput * lines_per_space_belt
# e.g. 720 * 12 = 8640 shapes/min per Space Belt connector
```

`ExteriorConnectionPlan` fields `terrain_upper_bound_per_min` (A) and `planning_target_per_min` (C) remain as in layer-stack spec; **C** sizes `required_connectors`.

### 2.2 Edge-weighted count distribution

```python
def distribute_connector_counts(
    total: int,
    edge_slots: dict[CardinalEdge, list[Coord]],
) -> dict[CardinalEdge, int]:
    edges = [
        CardinalEdge.NORTH,
        CardinalEdge.EAST,
        CardinalEdge.SOUTH,
        CardinalEdge.WEST,
    ]

    lengths = {edge: len(edge_slots[edge]) for edge in edges}
    perimeter = sum(lengths.values())

    if total <= 0:
        return {edge: 0 for edge in edges}

    if perimeter <= 0:
        raise NoConnectorSlotsError

    raw = {edge: total * lengths[edge] / perimeter for edge in edges}

    counts = {edge: math.floor(raw[edge]) for edge in edges}

    remaining = total - sum(counts.values())

    order = sorted(
        edges,
        key=lambda edge: (
            -(raw[edge] - counts[edge]),
            -lengths[edge],
            edges.index(edge),
        ),
    )

    for edge in order[:remaining]:
        counts[edge] += 1

    return counts
```

### 2.3 Even slot selection within each edge

```python
def choose_even_slots(slots: list[Coord], count: int) -> list[Coord]:
    if count <= 0:
        return []

    if count > len(slots):
        raise InsufficientConnectorSlotsError

    selected: list[Coord] = []
    used_indices: set[int] = set()
    L = len(slots)

    for i in range(count):
        # Explicit half-up integer rounding (NOT Python round() banker's rounding).
        numer = (i + 1) * (L + 1)
        denom = count + 1
        idx = (numer + denom // 2) // denom - 1
        idx = max(0, min(L - 1, idx))

        if idx in used_indices:
            idx = nearest_unused_index(idx, L, used_indices)

        used_indices.add(idx)
        selected.append(slots[idx])

    return selected
```

`nearest_unused_index` (normative): scan `idx+1`, `idx-1`, `idx+2`, `idx-2`, … until unused; on equal distance prefer **lower** index.

Corner exclusion is **not** a separate rule; `VOID_DEEP_SLOTS_V1` supersedes rim-corner filtering.

### 2.4 Planned connector assembly

For each edge with `k = counts[edge]`:

```text
chosen = choose_even_slots(candidate_slots_by_edge[edge], k)
```

For each `void_coord` in `chosen` (stable global order: N, E, S, W, then edge sort key):

```text
rotation = FIELDWARD_ROTATION_BY_EDGE[edge]
layout_t = default_exterior_connector_layout_t(transport_kind)  # base tile only
connector_id = ext_conn_{ii}  # zero-padded, deterministic
```

`layout_t` MUST NOT encode direction unless `game_data` explicitly requires directional
`layout_t` names (e.g. `SpaceBelt_East`). Direction is carried by `rotation` under `R0_E_CW`.

Append to `ExteriorConnectionPlan.planned_connectors`.

---

## §3 — Sprite rotation and Lab rendering

### 3.1 Rotation convention `R0_E_CW`

```python
ROTATION_BY_DIRECTION = {
    Direction.EAST: 0,
    Direction.SOUTH: 1,
    Direction.WEST: 2,
    Direction.NORTH: 3,
}
```

### 3.2 `FIELDWARD_FACING_V1`

| Edge bucket | Void location | Sprite faces | Rotation |
|-------------|---------------|--------------|----------|
| `N` | north of field | South | `1` |
| `E` | east of field | West | `2` |
| `S` | south of field | North | `3` |
| `W` | west of field | East | `0` |

```python
FIELDWARD_ROTATION_BY_EDGE = {
    CardinalEdge.NORTH: 1,
    CardinalEdge.EAST: 2,
    CardinalEdge.SOUTH: 3,
    CardinalEdge.WEST: 0,
}
```

**Invalid (forbidden in tests and implementation):**

```python
# INVALID — mixed outward/fieldward directions
{
    CardinalEdge.NORTH: 1,
    CardinalEdge.EAST: 0,
    CardinalEdge.SOUTH: 2,
    CardinalEdge.WEST: 3,
}
```

### 3.3 Lab rendering (deliverable B)

| Layer | Coordinate | Content |
|-------|------------|---------|
| White marker | `void_coord` | `overlay_role=planned_exterior_connector` (static CSS; not rose rim SVG) |
| Replay sprite | `void_coord` | `tile_type` = `SpaceBelt_*` or `SpacePipe_*`, `rotation` per `FIELDWARD_FACING_V1` |
| Metrics | — | `frame.metrics.exterior_connector_plan` |
| Frozen replay | — | `track_metrics.frozen_exterior_connector_plan` (same semantic value on L2+ frames) |

```text
marker_coord = connector.void_coord
sprite_coord = connector.void_coord
```

Display from **Layer 2 complete** onward on the solver timeline. v1: no separate toggle (optional follow-up: `lab-exterior-connector-highlight`).

### 3.4 Metrics wire

```json
{
  "exterior_connector_plan": {
    "version": "exterior_connector_plan.v1",
    "slot_rule": "VOID_DEEP_SLOTS_V1",
    "placement_rule": "EDGE_WEIGHTED_EVEN_SPACING_V1",
    "rotation_rule": "FIELDWARD_FACING_V1",
    "rotation_convention": "R0_E_CW",
    "required_connector_count": 9,
    "planned_connector_count": 9,
    "counts_by_edge": {
      "north": 3,
      "east": 2,
      "south": 2,
      "west": 2
    },
    "planned_connectors": []
  }
}
```

Connector row:

```json
{
  "connector_id": "ext_conn_00",
  "void_coord": {"x": 10, "y": -25},
  "edge": "north",
  "layout_t": "SpaceBelt_Forward",
  "rotation": 1,
  "capacity_per_min": "8640",
  "coords": [{"x": 10, "y": -25}]
}
```

Enum wire: `edge` uses lowercase slug (`north` | `east` | `south` | `west`); `failure_reason` / shortfall uses existing `ExteriorConnectionShortfallReason` StrEnum only.

---

## §4 — Tests

### 4.1 Slot depth

| Test | Assertion |
|------|-----------|
| `test_void_depth_excludes_rim_adjacent` | depth `1–4` void cells are not candidates |
| `test_void_depth_includes_at_5` | depth `5` void cell is included |
| `test_shallow_void_side_zero_slots` | side with max depth `<5` has `edge_len=0` |
| `test_void_depth_bfs_only_through_external_void` | BFS never steps through field or non-external cells |

### 4.2 Edge bucket

| Test | Assertion |
|------|-----------|
| `test_void_deep_slot_edge_from_bfs_source` | edge bucket equals BFS `source_edge` |
| `test_no_global_nearest_field_bucket` | concave fixture does not use Manhattan nearest-field bucketing |
| `test_candidate_slot_order_by_edge` | `N:x↑`, `E:y↑`, `S:x↓`, `W:y↓` |

### 4.3 Distribution

| Test | Assertion |
|------|-----------|
| `test_edge_weighted_count_distribution` | sum equals N; deterministic split |
| `test_edge_weighted_distribution_ignores_zero_slot_edge` | zero-slot edge receives count 0 |
| `test_choose_even_slots_interior` | indices avoid endpoints when possible |
| `test_insufficient_slots_fail_closed` | slots `< N` → `NO_FEASIBLE_CONNECTOR_SITES` |

### 4.4 Rotation

```python
def test_connector_rotation_fieldward_mapping() -> None:
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.NORTH] == 1
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.EAST] == 2
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.SOUTH] == 3
    assert FIELDWARD_ROTATION_BY_EDGE[CardinalEdge.WEST] == 0


def test_rotation_convention_r0_e_clockwise() -> None:
    assert ROTATION_BY_DIRECTION[Direction.EAST] == 0
    assert ROTATION_BY_DIRECTION[Direction.SOUTH] == 1
    assert ROTATION_BY_DIRECTION[Direction.WEST] == 2
    assert ROTATION_BY_DIRECTION[Direction.NORTH] == 3
```

Snapshot golden must include: `connector_id`, `void_coord`, `edge`, `layout_t`, `rotation`, `capacity_per_min`, `coords`.

### 4.5 Lab timeline

| Test | Assertion |
|------|-----------|
| `test_lab_timeline_exterior_connector_metrics` | L2+ frame has `metrics.exterior_connector_plan` |
| `test_lab_marker_uses_void_coord` | white marker at `void_coord` |
| `test_lab_sprite_uses_same_void_coord` | sprite at same `void_coord` |
| `test_lab_sprite_rotation_uses_fieldward_mapping` | overlay `rotation` matches `FIELDWARD_ROTATION_BY_EDGE` |
| `test_frozen_exterior_connector_plan` | frozen metrics persist after L2 |

### 4.6 Gates (existing PR-2)

- `GATE-LS-L2-CAP`: no belt/pipe cap literals in `layer_02_exterior_transport/`
- Missing EVTC row → `MISSING_EVTC_ROW` or stack `LAYER_FAILED_CLOSED`, not uncaught `LookupError`

---

## §5 — Implementation map (informative)

| Component | Path |
|-----------|------|
| Slot BFS + distribution | `layers/layer_02_exterior_transport/slots.py`, `placement.py` |
| Plan DTO | `layers/layer_02_exterior_transport/plan.py` |
| Layer run | `layers/layer_02_exterior_transport/run.py` |
| Timeline enrichment | `services/lab_replay_timeline_payload.py` (or dedicated enricher) |
| Lab CSS | `assets/css/input.css` — `.lab-planned-exterior-connector` |
| Lab JS | `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` |

---

## Final normative wording

```text
Layer 02 exterior connector placement uses VOID_DEEP_SLOTS_V1 plus
EDGE_WEIGHTED_EVEN_SPACING_V1 plus FIELDWARD_FACING_V1.

A connector slot is an external_void coordinate whose void_depth from
outer_rim_field is at least 5. Depth and edge bucket are assigned by
deterministic multi-source BFS from rim-adjacent external_void seeds.

The connector anchor is void_coord. Lab marker and replay sprite both render
at void_coord.

Rotation convention is R0_E_CW:
  R=0 East, R=1 South, R=2 West, R=3 North.

Connector sprites use FIELDWARD_FACING_V1:
  north edge → rotation 1
  east edge  → rotation 2
  south edge → rotation 3
  west edge  → rotation 0
```

---

## References

- [Layer stack design](2026-05-27-asteroid-lab-algorithm-layer-stack-design.md)
- [Terrain rim highlight](2026-05-25-reconstruction-complete-terrain-rim-highlight-design.md) — observability only; rose SVG separate from white connector marker
- [`exterior_transport_capacity.py`](../../../django_apps/game_data/services/exterior_transport_capacity.py) — EVTC SoT
- [Shapez 2 Wiki — Space transport](https://shapez2.wiki.gg/wiki/Space_Pipe) (community reference; EVTC DB wins on numeric caps)
