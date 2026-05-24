---
status: ARCHIVED
owner: asteroid-lab
last_reviewed: 2026-05-23
supersedes: []
superseded_by: documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md
related_epics: [PR-F coordinate extinction]
---

> **ARCHIVED (PR-F, 2026-05):** Dense server `(server_x, server_y)` and `server_coords.py` are **removed** from product code. Use island-local coords: [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](research_shapez2_copy_json_island_local_coords_2026-05-23.md). Normative spec: [`docs/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md`](../../docs/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md).

# Asteroid Lab: Server Coordinate System and Layout Fingerprint (Decision, Historical)

**Type**: Implementation memo (not CANON). Read with topology·Lab UI: [`documents/ai/plan_asteroid_reconstruction_topology_2026-05-16.md`](../ai/plan_asteroid_reconstruction_topology_2026-05-16.md), [`documents/ai/lab_map_rendering_contract.md`](../ai/lab_map_rendering_contract.md).

## Purpose

- Shapez2 decode **raw `X`/`Y`** are **copy JSON island-local** values (omitted → `0`; not world/asteroid absolute). Canonical: [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](research_shapez2_copy_json_island_local_coords_2026-05-23.md).
- **Keep** island-local raw for game·regeneration·debug.
- **Internal computation**: layout hash·`decoded_json` attachment·Lab grid (when possible) used **`server_x` / `server_y`**.
- **Transport BFS (`existing_layout_inspection`)** kept **raw `iter_four_neighbors`**. Rank `dense_x` can collide on consecutive positive raw `X` (e.g. 1 and 2), so server-grid 4-neighbors alone may diverge from existing observations.
- **coord_system** string: `server_bbox_right_bottom_dense_x_v1`

## raw x → dense x (no x == 0 column)

- Entries with `raw_x == 0` are a non-existent column; dense conversion **does not attach `server_x`/`server_y`** to those entries (existing `X`/`Y` unchanged).
- Formulas:
  - `raw_x < 0` → `dense_x = (raw_x + 1) // 2`
  - `raw_x > 0` → `dense_x = (raw_x - 1) // 2 + 1`

## bbox-based server coordinates (map-local, positive integers)

- Map = bbox of entire `BP.Entries` for that decode.
- `max_dense_x = max(dense_x)`, `min_raw_y = min(Y)`, `max_raw_y = max(Y)` (valid entries only).
- **server_x** = `max_dense_x - dense_x` → **rightmost column is `server_x == 0`**.
- **server_y** = `raw_y - min_raw_y` → **bottom row is `server_y == 0`** (assumes raw Y increases upward).  
  - If game confirms opposite, switch to `server_y = max_raw_y - raw_y` and update this document.

**Note**: `server_x`/`server_y` are **project-internal coordinates bound to that map bbox**, not Shapez2 global coordinates. Same raw cell's server values may change if map bbox changes.

## Difference from `visual_col` / Lab JS `visualCol`

- Legacy Lab `visual_col` (negative raw x as-is, positive as `x-1`) **differs numerically** from this server coordinate system.
- New paths use **rank-based `dense_x` + bottom-right origin bbox** only for `server_*` and fingerprint.
- Transition: UI prefers `server_x`/`server_y` when present, else legacy `visualCol`/raw fallback.

## Hash Field Roles

| Field | Meaning |
|------|------|
| `content_sha256` | **Input bytes** identity such as original copy code |
| `layout_fingerprint` | SHA-256 of canonical map on **bbox-normalized server coordinates**. Same relative pattern translated with bbox may yield **same hash**. |
| `absolute_layout_fingerprint` | SHA-256 of canonical on **dense_x + raw_y** (no bbox translation). Use when comparing position in map globally. |

Canonical JSON includes **`schema`**, **`coord_system`** (and agreed `origin`/`axis`/`bbox`); **do not hash without coord_system**. Fingerprint payload **does not include raw x/y**.

## Implementation Locations (Summary)

- Pure logic: `django_apps/asteroid_lab/snapshots/server_coords.py`, `layout_fingerprint.py`
- Attachment timing: right after decode + normalize, before `AsteroidMapInput.decoded_json` save
- DTO: `DecodedCellDTO.server_x` / `server_y`
