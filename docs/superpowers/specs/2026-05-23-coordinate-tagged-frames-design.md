# Coordinate Tagged Frames — Design Spec

**Status:** Approved 2026-05-23 · **PR-F completed 2026-05** (dense server bridge removed from product code)  
**Owner:** asteroid-lab / domain (Dominic) · implementation (Denny adapters + solver consumers)  
**Epic branch (suggested):** `fix/coordinate-tagged-frames` or `refactor/coord-frames-strangler`  
**Out of scope on RTTP branch:** PR-E / PR-F (see §RTTP branch policy)

**Related (CANON / ACTIVE):**

- [`documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md`](../../../documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md)
- [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../../../documents/research/research_blueprint_grid_coordinates_2026-05-10.md)
- [`docs/domain/asteroid_coord_transform_spec.md`](../../domain/asteroid_coord_transform_spec.md)
- [`documents/Algorithm/asteroid_lab_01_optimization_input.md`](../../../documents/Algorithm/asteroid_lab_01_optimization_input.md)
- [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../../../documents/Algorithm/asteroid_lab_03_candidate_generator.md)
- [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)
- RTTP (symptom-only overlap): [`2026-05-22-rttp-hybrid-c-layout-design.md`](2026-05-22-rttp-hybrid-c-layout-design.md)

**Implementation plan:** [`../plans/2026-05-23-coordinate-tagged-frames.md`](../plans/2026-05-23-coordinate-tagged-frames.md)

---

## Problem

Copy JSON **island-local** `(X,Y)` semantics are proven (in-game paste, regression fixture). **World / reconstruction** map semantics are documented separately (`x == 0` column absent; `1 ↔ -1` east jump). **Historical (pre–PR-F):** Server dense `(server_x, server_y)` was a derived bbox used as `Coord`. That bridge is **removed**; product paths use **island-local** `(x, y)` (`CoordFrame.ISLAND_RAW`).

**Current contract:** `OptimizationInput.coord_frame` defaults to `ISLAND_RAW`. Replay/Lab project island cells with identity projection. World map (`x==0` absent) remains a separate frame for reconstruction transport only.

## North star (end state) — ACHIEVED (PR-F, 2026-05)

Dense server bridge **removed from product code**. Table records the migration mapping:

| Removed at completion | Replaced by |
|-----------------------|-------------|
| `server_coords.py` bridge (`attach_server_coords`, `server_xy_for_raw_xy`, `raw_x_to_dense_index` on algorithm paths) | `IslandRawCoord` and/or `WorldRawCoord` only |
| `DecodedCellDTO.server_x` / `server_y` (wire + semantics) | Island or world tagged coords + `cell.x`/`cell.y` as island-local where applicable |
| `Coord` = dense server tuple in `OptimizationInput`+ | Single `CoordFrame` on `OptimizationInput` (PR-E) then typed coords (PR-F) |
| `lab_xy_from_server_xy`, JS dense mirror | Direct island/world → screen tile mapping |
| `coord_system=server_bbox_left_bottom_dense_x_v1` fingerprints | New `coord_system` version keyed to chosen raw frame |

Tagged types are a **strangler**, not the destination. `ServerCoord` exists only until PR-F deletes it.

## Goal (migration means)

Introduce **explicit tagged coordinate types** and a **strangler migration** that:

1. Preserves **island-local truth** at decode/export boundaries.
2. Preserves **world map invariants** at reconstruction / transport BFS boundaries.
3. **Deprecates** `ServerCoord` / `server_x` / `server_y` without deleting until equivalence is proven.
4. Allows **one canonical frame** on `OptimizationInput` only after the **proof gate** (PR-E).
5. **Deletes** all server dense artifacts in **PR-F** once PR-E is stable (north star).

## Non-goals

| Item | Rationale |
|------|-----------|
| Untagged `Coord = tuple[int,int]` as “raw” during migration | Silent frame mixing |
| `island → world` adapter before proof gate | Unproven equivalence |
| Server bridge removal on RTTP branch | Coordinate epic PR-F only |
| Merging **gene canonical E** into raw types | Orthogonal rotation algebra |
| Replay / metrics as algorithm input | Existing forbidden shortcut |

---

## Approved approach

**Approach 1 — Tagged newtypes + strangler** (approved). Do **not** promote a single untagged raw `Coord` until world↔island equivalence tests pass.

---

## Type model (§1)

| Type | Meaning | Neighbor contract | `x == 0` |
|------|---------|-------------------|----------|
| `IslandRawCoord` | Copy JSON / paste-local `X`,`Y` | `neighbors4_island`: `(x±1,y)`, `(x,y±1)` | **Valid** |
| `WorldRawCoord` | Asteroid / lab world evidence | `asteroid_map_coords`: `left_of` / `right_of`, `y±1` | **Forbidden** (`__post_init__` raises) |
| `ServerCoord` | **REMOVED** (PR-F) — do not reintroduce | — | — |
| `GeneLocalCoord` | Canonical-E gene offsets | `rotate_offset` + anchor translate | N/A (not map tile) |

**Module home (normative target):** `django_apps/asteroid_lab/snapshots/coord_frames.py`

```python
from enum import StrEnum

class CoordFrame(StrEnum):
    """Reserved names for OptimizationInput (PR-E). Do not introduce coord_system / frame / space duplicates."""

    SERVER_DENSE = "server_dense"
    ISLAND_RAW = "island_raw"
    WORLD_RAW = "world_raw"
```

**PR-E note:** `OptimizationInput.coord_frame: CoordFrame` is introduced only in PR-E when the proof gate is green. Until then, **document-only** reservation of `CoordFrame` names — no DTO field on `OptimizationInput`.

**Legacy aliases (migration):**

- `grid_contract.Coord` → treat as `ServerCoord` semantics until PR-F; re-export from `coord_frames` when PR-A lands.
- `reconstruction/grid.Coord` → rename meaning to `WorldRawCoord` (behavior + tests, not underscore-only rename).

**Gene layer:** `GeneTemplate` / `project_gene_placement` stay on canonical E; only **anchor** type changes when a single map frame is promoted (PR-E/F).

---

## Boundary rules (§2)

| Transform | Until proof gate | After proof gate (PR-E/F) |
|-----------|------------------|---------------------------|
| decode → `IslandRawCoord` | **Required** at copy boundary | Same |
| `attach_server_coords` → `ServerCoord` | Allowed, **deprecated** | Remove |
| `server_xy_for_raw_xy` | Allowed at listed creation sites only (§5) | Remove |
| `island → world` | **Forbidden** (no adapter) | Single module `prove_island_to_world` or fixture-tagged exception |
| `world → server` | Reconstruction legacy | Remove |
| `server → island` (`lab_xy_from_server_xy`) | Replay/UI adapter only | Remove |
| algorithm internal raw↔server | **Forbidden** (unchanged) | **Forbidden** |

**JSON serialization boundary:** `dict` with `"x"`/`"y"` or `"X"`/`"Y"` keys is allowed **only** at HTTP/JSON/replay wire encode-decode. Immediately after parse, promote to a tagged type.

### No silent tuple (AST gate — reviewer condition §2)

In packages:

- `django_apps/asteroid_lab/optimization/**`
- `django_apps/asteroid_lab/reconstruction/**` (except JSON ingest helpers)
- `django_apps/asteroid_lab/replay/**` (projection adapters)

**MUST NOT** pass `tuple[int, int]` or `dict[str, int]` (`{"x":…,"y":…}` / server fields) as if they were a map `Coord` between functions.

**MUST** use `IslandRawCoord`, `WorldRawCoord`, or `ServerCoord` (or explicit `GeneLocalCoord` for gene offsets).

Enforcement:

1. **mypy** — typed parameters on new/changed public APIs in PR-A+.
2. **AST test** — `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py` (see implementation plan): scan listed trees for patterns that assign or annotate bare `Coord = tuple[int,int]` in new code paths and for forbidden helper names crossing into `optimization` without `coord_frames` import.

Existing bare tuples may remain until touched; **new** edits in gated paths must use tagged types.

---

## PR sequence (§3)

| PR | Scope | RTTP overlap |
|----|--------|--------------|
| **PR-A** | `coord_frames.py`, `CoordFrame` enum (docs + types), re-exports; **no behavior change** | Allowed |
| **PR-B** | Decode/export: `IslandRawCoord` on copy path; mark `server_x`/`server_y` deprecated in docs/types | Allowed |
| **PR-C** | Reconstruction: `WorldRawCoord` in topology/BFS; `ServerCoord` only via legacy attach | Allowed |
| **PR-D** | Proof pack: island/world invariants + equivalence tests (**may stay red** — documents gap) | Tests only |
| **PR-E** | Gate: `OptimizationInput.coord_frame: CoordFrame` + single frame cells — **only if PR-D green** | **Forbidden** |
| **PR-F** | Remove `server_coords` bridge, bump `coord_system` fingerprint, flip algorithm docs/invariants | **Forbidden** |

**Do not** mix PR-E/F with RTTP overlay fixes.

---

## Proof gate (§4)

`OptimizationInput` may carry `coord_frame != SERVER_DENSE` only when **all** pass:

| ID | Requirement | Anchor test / doc |
|----|-------------|-------------------|
| G1 | Island paste truth | `test_copy_json_island_local_coords.py` |
| G2 | World map invariants | `test_asteroid_map_coords.py` |
| G3 | Equivalence fixtures | `test_coordinate_frame_equivalence.py` — **world track** (xfail until `island_to_world` adapter); **island-paste track** via `coord_proof_policy.py` (`ISLAND_PASTE_ONLY` → may use `CoordFrame.ISLAND_RAW` without world proof) |
| G4 | No silent tuple in gated paths | `test_coordinate_frame_ast_gate.py` |
| G5 | Algorithm docs updated | `asteroid_lab_01`, `asteroid-lab-invariants.mdc` |

If G3 fails: gate stays closed; keep `SERVER_DENSE` as runtime canonical; do **not** add untagged raw `Coord`.

---

## Server deprecation (§5) — COMPLETE (PR-F)

- **Deleted:** `django_apps/asteroid_lab/snapshots/server_coords.py`, dense server unit tests, Lab `server_*` HUD/wire.
- **Forbidden in product code:** `server_x`, `server_y`, `server_xy_params`, `attach_server_coords*`, `server_xy_for_raw_xy`, `lab_xy_from_server_xy` (AST: `test_coordinate_frame_ast_gate.py`).
- **Legacy persisted JSON:** may still contain `server_*` keys; readers **ignore** for display and algorithm input. No migration script in PR-F.

---

## UI / RTTP (§6)

**RTTP / current branch (symptom relief only):**

- Overlay labels cells with island-local `(x, y)`.

**PR-F (done):**

- `OptimizationInput.coord_frame` default `ISLAND_RAW`.
- `lab_xy_from_server_xy` and dense HUD **removed** from Lab JS.

---

## RTTP branch policy (reviewer condition §3)

On branch `feature/rttp-hybrid-c` (or any RTTP work):

| Allowed | Forbidden |
|---------|-----------|
| Consume **tagged** coord DTOs and projection **labels** in replay/UI adapters | Change `OptimizationInput` canonical frame |
| PR-A–C type imports and display-only tagging | Remove or bypass `server_coords` bridge |
| Read `CoordFrame` names in comments/docs | Introduce `island_to_world` equivalence adapter |
| | Touch algorithm input boundaries for coordinate proof |
| | Merge PR-E / PR-F |

Replay remains **output-only**. Lab / optimization replay stays **single timeline**; RTTP must not repoint solver or replay wiring to unproven frames ([`asteroid_lab_09_replay_timeline`](../../../documents/Algorithm/asteroid_lab_09_replay_timeline.md)).

---

## Tests & docs (§7)

| Artifact | Action |
|----------|--------|
| This spec | Normative |
| [`../plans/2026-05-23-coordinate-tagged-frames.md`](../plans/2026-05-23-coordinate-tagged-frames.md) | Bite-sized PR-A–F tasks |
| `docs/domain/asteroid_coord_transform_spec.md` | Add tagged-frame table; mark server-only algorithm path deprecated |
| `documents/Algorithm/asteroid_lab_01_optimization_input.md` | PR-E: `coord_frame` + single-frame rule |
| `.cursor/rules/asteroid-lab-invariants.mdc` | Tagged boundaries; gate wording |
| `documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md` | Link to this spec |

---

## Risks

| Risk | Mitigation |
|------|------------|
| `Coord` name overload during migration | `CoordFrame` enum reserved; typed aliases |
| Equivalence never provable | Stay on `SERVER_DENSE`; island/world remain tagged at boundaries only |
| RTTP PR mixes PR-E/F | RTTP policy table §RTTP branch policy |
| AST gate false positives | Allowlist JSON parse helpers; narrow scanned paths |

---

## Decision log

| Date | Decision |
|------|----------|
| 2026-05-23 | Approach 1 approved; dual tagged frames until proof gate |
| 2026-05-23 | `CoordFrame` names reserved pre–PR-E |
| 2026-05-23 | AST gate for silent tuple/dict coords |
| 2026-05-23 | RTTP overlap narrowed to PR-A–C consumption only |
| 2026-05 | PR-F: `server_coords.py` removed; island-local canonical for Lab/replay/optimization default |
