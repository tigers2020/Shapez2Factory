# Crystal System (Mechanics Summary)

Purpose: align **Crystal as separate from normal painted parts** and generation, clusters, and shatter propagation in solver and UI. Need not match game 1:1; cross-verify rule details by patch and measurement.

## Source Trust

| Source | Content | Trust |
| --- | --- | --- |
| Shapez 2 Wiki search | Crystal Generator fills gaps and pins with crystal up to highest used layer | High (wiki; cross-verify) |
| Shapez 2 Shapes Wiki search | Breaking crystal connectivity shatters entire connected crystal cluster | High (wiki) |
| Steam community | floating crystal, pin/gap, cluster breaking discussion | Medium (user experiments) |

---

## Core Definition

Crystal is a **special fill material** distinct from Circle/Rectangle, etc. Solver view:

```text
Crystal = part filling empty (gap) or pin cell with crystal (kind=c, color=color code)
```

Code encoding: one cell is a two-char token. Crystal is `c` + one color char (e.g. cyan → `cc`). Distinguish from normal red circle `Cr`, etc.

---

## 1. Crystal Generator (Generation)

Inputs: target **shape** + **color (color fluid color code)**.

### Recipe Graph (Wire Types)

In graph validation **material / fluid** are **wire carriers**, not "crystal material" in the game sense.

- **material**: connection from normal **shape** node (`shape_code` geometry flow).
- **fluid**: connection from **pure-color fluid** node with `source_carrier=fluid`.

Crystal Generator node is one of:

1. **`crystal_color` non-empty** → **1 input** (one shape line, material only). Color from node field.
2. **`crystal_color` empty (or whitespace)** → **same as Painter**: top `in-1` (slot `1`) **fluid**, bottom `in` target **shape (material)**. Color read from fluid ([`pure_fluid_color`](../../django_apps/shapez_solver/services/fluid_semantics.py)).

Domain operation signature remains "shape + one confirmed color char"; with 2 wires the graph aligns fluid and shape wires before [`apply_operation` … CRYSTAL_GENERATOR](../../django_apps/shapez_solver/services/operation_semantics.py).

Behavior (this repo, [`crystal_fill_gaps_and_pins`](../../django_apps/shapez_core/domain/crystal_geometry.py)):

1. Target layers up to `highest_used_layer_index(shape)`. Does **not** create new empty layers above that.
2. Each quadrant that is **empty (`--`) or pin (`P-`)** becomes crystal part of that color.
3. Normal shape parts are preserved.

Example (layer string order per [shape_encoding.md](shape_encoding.md)):

```text
Input Layer 0: `Ru--Ru--` (SW=Ru, NW=--, NE=Ru, SE=--) with cyan (`c`) → tokens `RuccRucc`.
Color: cyan → color code `c`, crystal token `cc`
```

Note:

```text
"Fill up to highest used layer" ≠ stack new empty layers on top.
```

Fully empty layers sandwiched in the stack model may exist; all `--` on that layer are crystal candidates.

---

## 2. Gap Filler Nature

Crystal is not mined directly from source but **fills existing gap/pin**. Target `RuccRucc` requires a prior step with **base shape including gap/pin + fluid color**.

---

## 3. Pin and Crystal

Generator can **turn pins into crystal**. To keep pins in the final result:

- Re-create pins with Pin Pusher **after** Crystal Generator, or
- Crystalize only at **intermediate stages** where pin→crystal is acceptable.

---

## 4. Crystal Cluster and Shattering

Wiki/community gist: **when one crystal breaks structurally, the entire connected crystal cluster shatters together.**

This repo's **approximation model** ([`crystal_geometry`](../../django_apps/shapez_core/domain/crystal_geometry.py)):

- **Same layer**: quadrants adjacent in ring (SW–NW–NE–SE perimeter).
- **Vertical**: same quadrant index on layer above/below.

BFS through crystal-only adjacency yields `connected_crystal_cluster`; `shatter_crystal_cluster` sets entire cluster to `--`.

Exact adjacency and shatter triggers (where cut line "touches") are **approximation before game confirmation**. Global shatter after Cut/Swap/Stack is future `OperationEngine` policy.

---

## 5. Floating Crystal

Forms like upper-layer crystal resting only on lower-layer gap may be **very restricted** to create/maintain. Solver should **exclude from reach candidates by default** or treat as high-cost separate search layer.

---

## 6. Per-Operation Notes (Design)

| Operation | Crystal Notes |
| --- | --- |
| Cutter | Cut may split cluster → shatter possible — rule TBD at implementation |
| Swapper | Half exchange risks cluster split/collision — prune candidates |
| Stacker | Crystal/support collision may shatter — validate/prune after stack |
| Pin Pusher | Pin preservation strategy needed when combined with crystalize order |

Current **operation engine** provides Generator fill and cluster/shatter **pure functions**; no automatic shatter on Cut/Swap/Stack yet.

---

## 7. Graph and Matching

Preview and target matching must **visually and by identifier** distinguish normal part / pin / crystal / gap. `gap == pin` does not always hold.

---

## 8. Implementation File Map (This Repo)

| Area | Path |
| --- | --- |
| Generation, cluster, shatter | [`django_apps/shapez_core/domain/crystal_geometry.py`](../../django_apps/shapez_core/domain/crystal_geometry.py) |
| Generator operation | [`OperationEngine`](../../django_apps/shapez_solver/services/operation_engine.py), [`apply_operation` … CRYSTAL_GENERATOR](../../django_apps/shapez_solver/services/operation_semantics.py) — color from node `crystal_color` or **2-wire top fluid (`pure_fluid_color`)** |
| Recipe graph recompute | [`recipe_graph_recompute`](../../django_apps/shapez_solver/services/recipe_graph_recompute.py) — `crystal_generator` is **1 or 2 input** by `crystal_color` (2-input fluid+material, same handle rules as Painter) |
| Part type | [`ShapePart.is_crystal`](../../django_apps/shapez_core/domain/shape.py), [`SHAPE_KINDS["c"]`](../../django_apps/shapez_core/domain/shape_catalog.py) |

---

## 9. Four-Line Summary

1. Crystal Generator fills **gap/pin** with specified-color crystal up to highest used layer.
2. Crystal is **fill material**, not a normal shape part.
3. Shatter rules needing **connected crystal cluster** removal require a cluster graph.
4. Pin·gap·floating combinations are hard — **staged solver** is safer.

## Related Documents

- [shapez2_crystal.md](shapez2_crystal.md) — wiki reference and links
- [shapez2_pin_support.md](shapez2_pin_support.md)
- [solver_operation_interface.md](solver_operation_interface.md)
