# Recipe Graph Editor — Plan (Revised 2026-05-04)

## Product Definition

**Look & feel** is the same as Lucidchart / draw.io / Figma flow / Node-RED.

- Node drag, line (edge) connection, zoom/pan, selection, context menu, block placement

**At its core**, it is not a drawing tool, but **an executable domain-specific visual graph editor**.

- Lucidchart: “Expressing people’s thoughts through pictures”
- This editor: “When a person manipulates the graph, **the system calculates and verifies the recipe meaning** and **recalculates intermediate output and whether the quantity and target are satisfied**.”

Axis of comparison: Like Node-RED / ComfyUI / Unreal Blueprint, **connections have meaning (data flow)**, but the domain is **Shapez2 recipe + solver**.

Recommended name: **Recipe Graph Editor** (can also be used as a superordinate concept for a dedicated UI for macro catalogs).

**Visual editing CRUD (Add, Modify, Delete)** — Fix once more the core values ​​expected by the user: **Add nodes/edges** on the canvas, **Modify** properties, connections, and placement, and **Delete** unnecessary elements. Fitting the graph using only JSON/API is an auxiliary method, and the main body of Lucidchart's sense is this CRUD loop.

---

## Architecture 4 Layers

### 1) Visual Layer (Lucidchart sense)

- Node position, selection, drag, connection handle, zoom/pan, (select) group
- **Visual editing CRUD**: Node/Edge **Add**, Selected item **Modify** (property/connection/coordinates), **Delete** — This is done on the same graph tile/wire visualization as the solver page **Live preview**.
- Operation node / shape node visual distinction — Maintain the direction of **reuse and generalization** of existing solver graph markup (`renderSolverGraph`, `initGraphViewport`)

### 2) Graph Model Layer (truth data)

Minimal concept (names organized into DTO/TS types in implementation):

- **ShapeNode**: `canonical_shape_code`, quantity, role (source / intermediate / target candidate)
- **OperationNode**: `OperationType`, port definition (number of inputs/number of outputs)
- **Edge**: from/to, kind(input|output), slot/label (port identification)
- (Extension) Placement/Style: `node_positions`, etc.

Storage: The existing `MacroRecipe` + `MacroRecipeStep` alone is not enough to express **arbitrary DAG + coordinates**. You must adopt one of the following:

- **Plan A (recommended)**: Put **nodes, edges, and coordinates** in one `MacroRecipe.graph_document` (JSON), and keep `MacroRecipeStep` as a **derived snapshot** for Pattern Lab backward compatibility or gradually discard it.
- **Plan B**: Normalized tables `GraphNode`, `GraphEdge` (high migration burden)

This amendment is based on **Plan A**.

### 3) Solver Layer (calculation/verification)

- **Graph validity**: Existing constraints such as DAG, port arity, number of inputs per `OperationType`, single-layer (if necessary), etc.
- **Operation result**: Input shape code(s) + operation → **Output canonical code(s)** — The domain is unified into the `shapez_core` + `OperationEngine` / [`apply_operation`(../../../../django_apps/shapez_solver/services/operation_semantics.py) series.
- **Propagation**: When one edge/node changes, **downstream nodes** are recalculated in topological order.
- **Verification**: Target satisfaction, throughput/quantity (if in scope) — The connection point with the existing solver service is explicitly set as a “port”

**Reality Constraints (Important)**: `apply_operation` currently only supports **some operations** (rotation, cutter, swapper, stacker, etc.). To open all `OperationType`s in the catalog in the editor, a **roadmap** that **extends the OperationEngine path** or places an operation-specific adapter is required. Phase 1 can be set to “Only supported operations are active in the editor.”

### 4) Sync Layer (UI ↔ Solver)

```text
User: Connect/Move/Delete/Change Operation
  → graph mutation (Graph Model)
  → validate + topological order
→ apply_operation(OperationEngine) for each OperationNode
→ Create/update new ShapeNode (intermediate result) + automatically create edges (“additional connections”)
  → UI refresh (Visual)
```

Put your needs in one line:

> **When connecting the base shape node and the operation node, the output is automatically calculated and added as a node (and connection), and when the output is connected to the next operation, the next result should also be automatically added and connected.**

This means **not a simple JSON slot string edit**, but that the connection graph has **execution semantics** and **downstream must always be synchronized** with the engine results.

---

## Operation algorithm (automatically calculated when connected)

1. The user connects the **number of** Shape nodes (or already calculated intermediates) to the **input edge** of the operation.
2. Determine whether the Sync Layer marks the corresponding OperationNode as **ready**: Required input arity is met, shape code can be parsed.
3. Execute **domain operation** for `OperationType` → Output tuple of canonical codes.
4. For each output:
- Update if there is an existing **Output Shape node**, without **Create a new Shape node**
- Operation **Output port → Shape node** **Automatically creates** edges (Needs UX decision on whether to make **the result look like it is connected** rather than “drawing a line” by the user, or confirm it after a ghost edge — the default is **Automatic solid edge + node spawn** meets the requirements)
5. Enqueue the downstream OperationNode **connected to the changed Shape node and repeat 2-4 times (until fixed point or abort on cycle/error).

**cycle·ambiguity**: As in the solver DAG premise **no cycles**; Document policies such as prohibiting partial execution when waiting for multiple inputs.

---

## Relationship with existing “macro staff catalog” plan

- The `graph_editor` (coordinates only) + `steps` double truth of the previous draft is rearranged so that **Graph Model becomes the main truth** in this revision.
- Pattern Lab / DB macro candidates place **compatibility strategies** in a separate checklist, such as deriving a summary of steps from **graph_document**, or initially saving only the graph** and reading Lab limitedly.

---

## Implementation steps (roadmap)

| Phase | Content |
|--------|------|
| P0 | 4-layer spec fixed, `graph_document` schema draft, supported `OperationType` list (per engine) |
| P1 | Visual: Solver Graph Component Reuse + Ports/Connection UX + **Visual Edit CRUD (Add/Modify/Delete)** Skeleton |
| P2 | Sync: Call `apply_operation`/Engine when connection is completed → Automatically create output node/edge and recalculate downstream |
| P3 | Verification: target/quantity, error UI, partial graph invalid display |
| P4 | Expansion of supported calculations, throughput linkage (separate service if necessary) |

## Development progress principles

- It is based on the **phase order (P0 → P4)**, and due to dependency, some backends and schemas are allowed to go up before the UI, but **visual editing CRUD** is explicitly filled as a requirement in P1 and P2.
- Even within one phase, verification is done **by dividing it into small units**, and progress is made **sequentially and conservatively** while maintaining a test and recalculation path to prevent regression (do not rush to expand the surface of the next phase).

---

## Output/Approval

- This document `documents/` is a revised version of the plan. Before implementation begins, the **Human Approval** gate follows the repository rules ([AGENTS.md](../../../../AGENTS.md)).
- Touch expected paths in implementation: `django_apps/shapez_solver/services/operation_semantics.py` extension, (new) `recipe_graph_*` services/DTO, `django_apps/web/static/...` graph module generalization, `MacroRecipe` migration.

---

## Open issue (recommended decision upon approval)

1. **Output automatic connection UX**: Whether to **always spawn the output from the engine as an automatic node+edge** or just preview it until the user “confirms” it.
2. **Storage unit**: One `graph_document` per recipe vs version history.
3. **Pattern Lab Synchronization**: The read path gives priority to the derived step (`try_pattern_macro_step_rows_from_graph_document`) from `graph_document`. **Write** match with DB `steps` is optional.

---

## Implementation progress (2026-05-04)

| Phase | Status | Notes |
|--------|------|------|
| P0 | **Partially done** | `MacroRecipe.graph_document` field + migration `0003`, schema constant [`recipe_graph_constants.py`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py) |
| P2 | **Partially done** | Server recalculation [`recipe_graph_recompute.py`](../../../../django_apps/shapez_solver/services/recipe_graph_recompute.py) (`validate_graph_document`, `recompute_graph_document`), staff `POST .../recipes/<id>/graph/recompute/?` (DB save when `commit`), Expose `recipe_graph_engine_operations` in catalog |
| P1 | **Partially done** | Solver graph: operation·shape **port**(wire); Details **Copy node id**; `painter` `paint_color` description; staff **edge append + wire**; **Pattern Lab reading motivation**: `graph_document`→derived steps first·`pattern_lab_steps` JSON. **Visual editing CRUD (node/edge addition/property/connection modification/delete) is incomplete — sequential reinforcement at P1·P2.** |
| P3 | **Partially done** | Graph target verification: `explain_pattern_family_mismatch` (same inventory as Pattern Lab + union of canonical quadrant rotation signatures); remove string cyclic `_cyclic_signatures`; Recalculation API·Graph badge·Staff issue list maintenance |
| P4 | **Partially done** | `painter` + **`color_mixer`**: `apply_operation` / `OperationEngine` / [`RECIPE_GRAPH_ENGINE_OPERATIONS`](../../../../django_apps/shapez_solver/services/recipe_graph_constants.py) / recalculate 2-input branch; `paint_color`·[`color_mix_semantics`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py)(MVP) |

**Progress Snapshot (Attachment):** [`recipe_graph_editor_progress_2026-05-04.md`](recipe_graph_editor_progress_2026-05-04.md)

Only operations supported by `apply_operation` are used for recalculation (rotation, cutter, swapper, stacker, **painter**, **color_mixer**).
