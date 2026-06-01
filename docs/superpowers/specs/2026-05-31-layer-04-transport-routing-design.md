# Layer 05 Transport Routing — Normative Design

> **Stack renumber (2026-05-31):** Canonical slug is `layer_05_transport_routing` (L5). Implementation package remains `layer_04_transport_routing/` until PR-2. Inner fill is L4 (`layer_04_inner_pattern_fill`). See [`2026-05-31-layer-stack-l4-l5-renumber-design.md`](2026-05-31-layer-stack-l4-l5-renumber-design.md).

**Status:** APPROVED (§1 2026-05-31; §2–§3 aligned with brainstorming)  
**Date:** 2026-05-31  
**Owner:** `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/` (physical path; canonical entry `run_layer_05_transport_routing`)  
**Supersedes:** disabled `layer_04_rim_bundle_placement` shim; amends L3 v2 non-goals  
**Related:** [`2026-05-31-layer-03-rim-placement-v2-design.md`](2026-05-31-layer-03-rim-placement-v2-design.md), [`documents/game_data/space_transport_identifiers.md`](../../../documents/game_data/space_transport_identifiers.md)

---

## Goal

Connect L3 `m_output_stub` cells to L2 `planned_connectors` with **same-kind** merge-aware weighted shortest routes, project `SpaceBelt_*` / `SpacePipe_*` tiles from ESWN I/O signatures, and emit the **sole authoritative** transport layer for replay/overlay.

## Non-goals

- Mix shape+fluid routing in one L4 run (`MIX_UNSUPPORTED` fail-closed v1).
- L3 placement re-selection or beam re-run.
- Lift tiles in routing v1 (catalog import only; projector forbids lifts).
- Using L3 `route_probe_path` as committed transport or render authority.
- Raw `documents/game_data/*.json` parsing inside core L4 (catalog port only).
- L2 EVTC per-minute capacity as L4 group capacity (separate M-bundle accounting unit).

## Architecture choice (locked)

```text
V1 slug: layer_04_transport_routing
R1: sequential source routing + trunk-as-goal attach (no traverse-through-trunk v1)
C1: JSON → SpaceTransportTileCatalog port → signature lookup
A: L3 route_probe_path witness-only; L4 sole transport authority
```

---

## Layer boundary

### L3 authoritative

- Committed M / extractor / extension equipment cells
- `m_output_stub`
- Provisional equipment overlay (not final belt/pipe tiles)

### L3 witness only (not authoritative for transport)

- `route_probe_path` on `CommittedRimSeedPlacement`
- L3 route probe / commit-time re-probe paths
- L3 `candidate_route_path` replay overlay kinds

### L4 authoritative

- Final `SpaceBelt` / `SpacePipe` route cells (`transport_tiles`)
- Merge / trunk `RouteGroup` capacity accounting (`source_load_m`)
- L4 weighted route cost under L4 cell weights
- ESWN input/output signature → `tile_id` + `rotation` (R0_E_CW)
- Replay/overlay **final transport** layer

### Witness rules (normative)

| ID | Rule |
|----|------|
| W1 | `route_probe_path` is L3 feasibility witness only; not committed transport |
| W2 | Witness paths must not reserve route cells for L4 |
| W3 | Witness paths must not contribute to L4 routed throughput |
| W4 | L4 may ignore all probe paths when building `Layer04RoutePlan` |
| W5 | L4 routing tests must pass when all `route_probe_path` are empty |

### Required L3 spec amendment

Add to `2026-05-31-layer-03-rim-placement-v2-design.md`:

- Non-goals: replace “Rim bundle packing role of L4 (remains disabled)” with “Final transport routing is Layer 04 (`layer_04_transport_routing`); L3 does not emit committed SpaceBelt/SpacePipe tiles.”
- New paragraph: L3 route probe / `route_probe_path` / replay route overlays are **feasibility witnesses only**; L4 is sole authority for final belt/pipe cells, groups, capacity accounting, sprite projection, and transport replay.

---

## Inputs

```python
Layer04Input:
    resource_kind: ResourceKind              # v1: single kind per run
    complete_map: ReconstructionCompleteMap
    exterior_plan: ExteriorConnectionPlan
    rim_result: IntegratedRimGreedyResult
    transport_catalog: SpaceTransportTileCatalog
```

Core converts `rim_result` → `tuple[Layer04SourceView, ...]` via adapter (routing engine never reads `IntegratedRimGreedyResult` directly).

```python
Layer04SourceView:
    placement_id: str
    m_output_stub: Coord
    source_load_m: int                      # L4 capacity unit
    throughput_factor: int                  # provenance; 4|8|12|16
    equipment_cells: frozenset[Coord]       # miner | extension
    route_probe_path: tuple[Coord, ...]     # witness only
```

**Assumption (v1):** `source_load_m = throughput_factor`. If EVTC/minute conversion diverges later, only the L4 source adapter changes—not the router.

`throughput_factor` must be persisted on `CommittedRimSeedPlacement` (L3 commit contract extension).

---

## Resource → transport

| L1 `resource_kind` | L4 `transport_kind` | Tile prefix | `unit_capacity_m` per connector |
|--------------------|---------------------|-------------|----------------------------------|
| `shape` | `space_belt` | `SpaceBelt` | 12 |
| `fluid` | `space_pipe` | `SpacePipe` | 72 |
| mixed | — | — | `MIX_UNSUPPORTED` |

`group.capacity_m = connector_count_in_group * unit_capacity_m` (M-bundle units; **not** L2 EVTC per-minute).

---

## Routing model (R1)

### Cell weights (A* / Dijkstra scoring)

```python
L4_CELL_WEIGHT = {
    "void": 1,
    "asteroid_field": 5,
    "e": 10,
    "m": 20,
}
```

### Search vs commit

| Terrain | Search weight | Commit |
|---------|---------------|--------|
| void | 1 | allowed |
| asteroid_field | 5 | allowed when game rule allows |
| e | 10 | **forbidden** except connector/port whitelist |
| m | 20 | **forbidden** except stub-boundary whitelist |

A* may score `e`/`m` for reachability; `commit_validator` rejects generic equipment overlap on `transport_tiles`.

**Allowed commit exceptions:** `m_output_stub` adjacency, L2 connector attachment cell, explicitly declared port cells.

### Same-kind merge (v1)

- Different transport kinds: hard conflict.
- Same-kind existing **trunk endpoint** cells: valid **goals**; path **stops on attach** (do not route through trunk interior in v1).
- Traversal cost on trunk: **not required to be 0**; v1 does not implement “walk along existing trunk.”

### Goals per source

```text
goals = connectors_with_remaining_capacity
      ∪ same_kind_trunk_attach_cells_with_remaining_capacity
```

### Source order (deterministic)

```python
sorted(sources, key=lambda s: (
    nearest_connector_astar_cost_estimate(s),
    -s.source_load_m,
    s.m_output_stub.x,
    s.m_output_stub.y,
    s.placement_id,
))
```

### A*

- Algorithm: A* with `h = manhattan(current, goal) * 1` (admissible).
- Tie-break heap key: `(f, g, path_len, goal_id, x, y)`.
- On success: commit path cells, union groups, add `source_load_m`, expose new trunk attach goals.

### Failure reasons

```python
class Layer04FailureReason(StrEnum):
    MISSING_L2_EXTERIOR_PLAN = "missing_l2_exterior_plan"
    EMPTY_L3_PACKAGE = "empty_l3_package"
    RESOURCE_KIND_MISMATCH = "resource_kind_mismatch"
    MIX_UNSUPPORTED = "mix_unsupported"
    NO_CONNECTOR_WITH_CAPACITY = "no_connector_with_capacity"
    ROUTE_NOT_FOUND = "route_not_found"
    CAPACITY_OVERFLOW = "capacity_overflow"
    COMMIT_OVERLAP_BLOCKED = "commit_overlap_blocked"
    CATALOG_MISSING_TILE = "catalog_missing_tile"
    UNSUPPORTED_IO_SIGNATURE = "unsupported_io_signature"
```

---

## Output

```python
Layer04RoutePlan:
    version: str
    resource_kind: str
    transport_kind: str
    routes: tuple[CommittedRoute, ...]
    groups: tuple[RouteGroupSummary, ...]
    transport_tiles: tuple[ProjectedTransportTile, ...]
    failures: tuple[Layer04Failure, ...]
    metrics: Layer04Metrics
```

Replay/overlay transport: **`transport_tiles` only**.

```python
ProjectedTransportTile:
    coord: Coord
    transport_kind: str
    tile_id: str
    rotation: int                         # R0_E_CW
    input_dirs: tuple[str, ...]          # E,S,W,N slugs
    output_dirs: tuple[str, ...]
    group_id: str
    source_route_ids: tuple[str, ...]
```

---

## Catalog (C1)

- Import from `research_unlocks.json` + `simulation_systems.json` paths documented in `space_transport_identifiers.md`.
- Normalize to `SpaceTransportTileCatalogEntry` with `TransportIoSignature` (ESWN bool masks, R0_E_CW).
- Core L4 uses `SpaceTransportTileCatalog` port only.
- Turn/Merger left-right: require visual oracle or definition snapshot before golden tests (Forward from ESWN only until oracle lands).

---

## PR slices

| PR | Scope |
|----|--------|
| L4-0 | This spec + DTOs + failure enum + L3 `throughput_factor` on commit + L3 spec amendment + slug |
| L4-1 | Catalog import + signature table + rotation contract tests |
| L4-2 | One source → one connector A* MVP, commit validator, no merge |
| L4-3 | Merge groups + capacity + trunk goals |
| L4-4 | Sprite projection (Forward/Turn/Merger minimum) |
| L4-5 | stack_runner wire, replay segment, metrics, W5 tests |

---

## Acceptance (representative)

- `test_layer04_ignores_route_probe_path` (W5): routing unchanged when probe paths empty.
- `test_layer04_commit_blocks_equipment_overlap`: no belt on generic `e`/`m`.
- `test_layer04_deterministic_tie_break`: golden path on fixed map.
- `test_layer04_mix_unsupported`: fail-closed on mixed resource kinds.
- Catalog: `test_space_transport_signature_r0_e_cw.py` rotation contract.

**Gates:** `powershell -File scripts/test_fast.ps1`, `ruff check .`, `mypy django_apps config src`, `black --check .`
