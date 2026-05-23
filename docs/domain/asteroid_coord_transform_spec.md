# Asteroid Lab — coordinate transform (canonical E → island map grid)

**Owner:** Dominic (domain) · **Implementation:** `django_apps/asteroid_lab/optimization/coord_transform.py`, `gene_template.py`, `gene_projection.py`  
**Status:** Phase 0 domain contract (v0) · **PR-F (2026-05):** island-local map grid; dense server removed  
**Consumers:** gene projection, placement materialization, `game_data` snapshot adapter (footprint/port rotation)

## Purpose

Gene topology and `game_data` building geometry are authored in a **building-local** frame with **canonical output facing E**. The optimization layer places bundles on the **island-local map grid** (`CoordFrame.ISLAND_RAW`) by rotating local offsets clockwise, then translating by an anchor (extractor island coord). This document is the normative spec for that transform; code must match it exactly.

**Out of scope here:** copy JSON serialize rules — [`copy_json_coords.py`](../../django_apps/asteroid_lab/snapshots/copy_json_coords.py). **Removed (PR-F):** dense server bbox attach (`server_coords.py`). Algorithm paths use **island `Coord` only** after normalize — never raw blueprint re-conversion.

## Coordinate frames

| Frame | Origin | Used by |
|-------|--------|---------|
| **Copy JSON island-local** | Pasted island `BP.Entries`; omitted `X`/`Y`/`R` → `0`; `X+1` right, `Y+1` down; **`X==0` valid**; tagged `IslandRawCoord` via `entry_island_raw_coord` | Game paste decode, export serialize; migration: [`2026-05-23-coordinate-tagged-frames-design.md`](../superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md) |
| **Canonical E (gene-local)** | Extractor at `(0, 0)`; bundle `output_dir == E` | `GeneTemplate`, `ExtensionAttachment` offsets |
| **Building-local (`game_data`)** | Per-variant footprint / connector import frame | `BuildingFootprintCell.x/y` in `AsteroidGameDataSnapshot` |
| **Island map grid (`Coord`)** | `CoordFrame.ISLAND_RAW`; algorithm input after normalize | `Coord`, materialized cells, fingerprints |
| **World / reconstruction map** | Asteroid evidence grid; **`x==0` column does not exist** | Transport BFS, reconstruction ([`research_blueprint_grid_coordinates_2026-05-10.md`](../../documents/research/research_blueprint_grid_coordinates_2026-05-10.md)) |

After `OptimizationInput` normalization, the algorithm layer must **not** convert copy JSON ↔ map grid again ([`asteroid_lab_01`](../../documents/Algorithm/asteroid_lab_01_optimization_input.md)).

## Canonical E gene storage

`GeneTemplate` is always stored in canonical E:

- `output_dir == Direction.E` (enforced in `GeneTemplate.__post_init__`).
- `extractor_offset == (0, 0)`.
- Example canonical offsets (belt gene): `fixed_output_transport_offset == (1, 0)`, `route_probe_start_offset == (2, 0)` — one and two cells **east** of the extractor in gene-local space.

```python
CANONICAL_OUTPUT_DIR: Direction = Direction.E
CANONICAL_EXTRACTOR_OFFSET: Coord = (0, 0)
CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET: Coord = (1, 0)
```

Rotation at placement time is **not** stored on the template; it is derived from the candidate’s target `output_dir` (or `rotation` argument to projection).

## Rotation helpers (`coord_transform.py`)

### Quarter-turn index

Clockwise quarter-turns from canonical E to a target facing:

```text
_DIRECTION_CW_ORDER = (E, S, W, N)
steps = index(target)   # E=0, S=1, W=2, N=3
```

`steps_from_canonical_e(target)` returns that index; unsupported directions raise `ValueError`.

### `rotate_offset(offset, steps)`

Rotate a gene-local offset around the origin by `steps % 4` quarter-turns **clockwise**:

```python
x, y = offset
for _ in range(steps % 4):
    x, y = y, -x
return (x, y)
```

### `rotate_direction(direction, steps)`

Rotate a cardinal `Direction` by the same number of CW quarter-turns using `_DIRECTION_CW_ORDER`.

## Island map placement

Placement is implemented in `gene_projection._translate` / `project_gene_placement`:

1. `steps = steps_from_canonical_e(rotation)` where `rotation` is the bundle’s output facing on the map grid.
2. For each gene-local offset `rel`: `(rx, ry) = rotate_offset(rel, steps)`.
3. **Map cell:** `(anchor_x + rx, anchor_y + ry)` with `anchor` = extractor island position.

```python
def _translate(anchor: Coord, rel: Coord, steps: int) -> Coord:
    rx, ry = rotate_offset(rel, steps)
    ax, ay = anchor
    return (ax + rx, ay + ry)
```

`project_gene_placement` applies this to `occupied_offsets`, extensions, `fixed_output_transport_offset`, and `route_probe_start_offset`. The returned `output_dir` is the requested `rotation` (not re-derived from template).

Equipment materialization (`placement_network_materializer`) uses the same `_translate(anchor, offset, steps)` for attachment offsets and sets miner/extension **rotation** to `steps` (0–3) on the server grid.

## `game_data` footprint and ports

- Footprint cells and connector positions in `AsteroidGameDataSnapshot` are **building-local** (see [`asteroid_game_data_snapshot.md`](asteroid_game_data_snapshot.md)).
- When a building variant is placed at server `(anchor_sx, anchor_sy)` with rotation `steps`, the adapter applies **`rotate_offset` + anchor add** to each local `(x, y)` — the same rule as gene offsets.
- Port compatibility checks use island map coords after rotation; extension parent/child edges use `grid_contract.neighbors4`.

## Copy JSON vs island map vs world (decode boundary)

| Frame | `X==0` / `x==0` | Notes |
|-------|-----------------|-------|
| Copy JSON island-local | **Allowed** | Not asteroid world position; relative layout inside paste |
| Island map grid (`Coord`) | Same semantics as copy local at lab boundary | Optimization / fingerprint after normalize |
| World / reconstruction map | **No `x==0` column** | Transport BFS only; do not mix with paste grid |

## Raw column rule (decode-only)

| Rule | Where |
|------|--------|
| Preserve island-local `X`/`Y` on decode (omitted → `0`) | `copy_json_coords`, reconstruction, export |
| **Removed:** dense server attach | PR-F — see archived research doc |
| Snapshot build, gene projection, route probe, commit | **Island `Coord` only** — no raw re-conversion |

Violating copy↔map grid conversion inside the algorithm layer after normalize is forbidden ([`asteroid-lab-invariants`](../../.cursor/rules/asteroid-lab-invariants.mdc)).

## Golden vectors

Reference offset: gene-local **`(1, 0)`** (canonical fixed-output transport stub).  
Reference direction: **`Direction.E`** before rotation.

### Offset rotation (`rotate_offset`)

| CW steps | ° (CW) | `rotate_offset((1, 0), steps)` | Δserver from anchor |
|----------|--------|--------------------------------|---------------------|
| 0 | 0° | `(1, 0)` | `(+1, 0)` |
| 1 | 90° | `(0, -1)` | `(0, -1)` |
| 2 | 180° | `(-1, 0)` | `(-1, 0)` |
| 3 | 270° | `(0, 1)` | `(0, +1)` |

Semantics: repeat `x, y = y, -x` for `steps % 4` iterations (matches `coord_transform.rotate_offset`).

### Direction rotation (`rotate_direction(Direction.E, steps)`)

| CW steps | Result direction |
|----------|------------------|
| 0 | E |
| 1 | S |
| 2 | W |
| 3 | N |

### Anchor worked example

- Anchor (extractor server coord): `(10, 5)`.
- Gene-local offset: `(1, 0)`.
- Target output facing: **S** → `steps = steps_from_canonical_e(Direction.S) = 1`.

```text
rotated_local = rotate_offset((1, 0), 1) = (0, -1)
server        = (10 + 0, 5 + (-1)) = (10, 4)
```

On the server grid, **+x is east** and **+y is south** (`cardinal_unit_toward`: `dy > sy` → `Direction.S`). One CW quarter-turn moves the `(1, 0)` stub from east of the extractor to **north** of it (Δy = -1), not south.

Table-driven tests for this table are planned in Phase 1 (`test_coord_transform_golden.py` per integration plan).

## Implementation map

| Concern | Module |
|---------|--------|
| `rotate_offset`, `rotate_direction`, `steps_from_canonical_e` | `genetic_sample/coord_transform.py` |
| Canonical E template invariants | `genetic_sample/gene_template.py` |
| Anchor + rotation → server cells | *(removed with solver — gene projection deleted)* |
| Equipment cells + extension rotation | *(removed with solver)* |
| Building-local snapshot (pre-rotation) | `contracts/game_data_snapshot.py` (consumer) |

## References

- [`asteroid_game_data_snapshot.md`](asteroid_game_data_snapshot.md) — building-local footprint ordering
- [ADR-004: game_data snapshot boundary](../adr/ADR-004-game-data-snapshot-boundary.md)
- [`asteroid-lab-invariants.mdc`](../../.cursor/rules/asteroid-lab-invariants.mdc) — raw vs server boundary
