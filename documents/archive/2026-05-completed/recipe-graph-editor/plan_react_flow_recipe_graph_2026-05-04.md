# React Flow / XYFlow based Recipe Graph Editor — Architecture/Migration Plan (2026-05-04)

> **Status**: Draft for planning/approval. It must pass through a human approval gate before implementation.
> **Premise**: Shift the existing staff graph UI (WebGL canvas + `solver_timeline` mount) towards **deprecation**, but preserve the storage format **`MacroRecipe.graph_document` domain contract** as much as possible.

---

## 0. Goals (Summary)

| Item | Content |
|------|------|
| **Remove** | WebGL-based node/wire rendering in the main graph editor |
| **Introduction** | React Flow (XYFlow) + HTML custom node + SVG edge |
| **Maintain** | Select node detailed/zoomed view, etc. **Only allows single WebGL/Three** preview |
| **Domain** | `operation → operation` Direct connection is prohibited, operation output goes through **intermediate(form)** |
| **Palette** | Document §4 Supported operations only (excluding LOGIC·UTILITY) |
| **UI Form** | Same area/layout as the enclosed **RECIPE GRAPH EDITOR** mockup (§2.1). |

---

## 1. Integration with code base

### 1.1 Existing domain (`graph_document`)

- node: `kind`: `"shape"` \| `"operation"`
- Shape role: `role`: `"source"` \| `"intermediate"` \| `"target"` ([`SolverShapeNode`](django_apps/shapez_solver/dto/solver_graph.py))
- edge: `kind`: `"input"` \| `"output"` (shape ↔ operation direction is verified by server/topology rules)

React Flow side **UI-only type** (`intermediate`/`output` node type) is mapped as follows.

| React Flow `nodeType` (suggested) | `graph_document` |
|------------------------------|------------------|
| `shape` (source material) | `kind: "shape"`, `role: "source"` |
| `operation` | `kind: "operation"`, `operation` field |
| `intermediate` | `kind: "shape"`, `role: "intermediate"` |
| `output` | `kind: "shape"`, `role: "target"` |

Edge's `input`/`output` and React Flow `source`/`target` handles are converted consistently from **adapter**.

### 1.2 Backend API (current — replaces document §7 example URL)

Before introducing the new `/api/recipe-graphs/`, **the existing staff API** is used as the contract.

| Use | Method·Path (example) |
|------|------------------|
| Page·Bootstrap | `GET` [`web:macro-pattern-graph`](django_apps/web/urls.py) |
| JSON recalculation/saving | `POST` `… /api/recipes/<pk>/graph/recompute/` ([`macro-pattern-staff-api-recipe-graph-recompute`](django_apps/web/urls.py)) |
| Recipe details | `GET/PATCH` `… /api/recipes/<pk>/` |

Payload field names continue to use **`graph_document`**. React Flow's internal state is **converted to domain format when serialized** and stored.

### 1.3 Relationship with server verification

- Authoritative verification/recalculation: [`validate_graph_document`](django_apps/shapez_solver/services/recipe_graph_recompute.py), [`recipe_graph_topology`](django_apps/shapez_solver/services/recipe_graph_topology.py), etc.
- The front `canConnect` / arity is **UX blocking**, and the final match is overwritten by the server response.

---

## 2. Final Architecture (After)

```text
Django template (graph page)
└─ React island (one root)
   └─ ReactFlowProvider
      ├─ GraphCanvas (XYFlow)
      │   ├─ ShapeNode / OperationNode / IntermediateNode / OutputNode
      │   └─ RecipeEdge (custom)
      ├─ OperationPalette
      ├─ InspectorPanel
      ├─ ValidationPanel
      └─ StatusBar

Selected / Expanded preview (selected area only)
└─ Existing Three.js / shape GLTF viewer — limited to 1-2 instances
```

Node Tiles: **WebGL prohibited** (SVG·CSS·Canvas2D mini preview).

### 2.1 Visual/Layout — Enclosed **RECIPE GRAPH EDITOR** Mockup and registration

When implemented, the **page form aims to be the same information area/hierarchy** as the accompanying mock-up image. (Not pixel-by-pixel replication, but **Area/Pattern/Style Language** alignment.)

| Zone | Mockup Requirements |
|------|----------------|
| **Theme** | Industrial/game editor tones such as dark mode, cyan, orange, purple, yellow points, thin border, monospace ID, etc. |
| **Header** | Left: Logo + title **RECIPE GRAPH EDITOR** + one-line subtitle (e.g. Create, preview and optimize shape recipes). Right: **Catalog**, **Edit metadata** (maintain existing staff URL). |
| **Left Palette** | Top **Search operations… ** input. Categories **SHAPE / COLOR / ROTATE / CUT / FLOW** and subcategories such as mockups (Base shape, Painter, Color mixer, …). **Small icon + label** for each item, card-style list. **Quick access** area at the bottom (i.e. a “drag to add quickly” drop zone — text tailored to the mockup). |
| **Main Canvas (React Flow)** | **Top overlay toolbar**: One-line recipe/wire guide, **View controls such as grid·snap·zoom%·Fit to screen**. **Background**: Grid (readability equivalent to mockup). **Node**: Rounded square, top icon·title·bottom **Node ID** (e.g. `MIX_01`), left **input**·right **output** port (small square handle). **Optional stage group** (mockup's CREATE & COLOR / TRIM & PREPARE / SPLIT & STACK, etc. purple, orange, teal **track header**) is not required for the domain, **the first stage is reproduced as a visual group** (parent node, annotation layer, or simple Y offset), and the **second stage** can be integrated with the layout engine. **Edge**: Smooth **Bezier curve**, preferably **stroke in the same color family as the group/stage** (custom `RecipeEdge`). **Right Outputs section**: A row of terminal nodes with the label **OUTPUTS** and a final **Output 1 (…)** — implemented in React Flow as a fixed right panel or cluster of `output` nodes in the same viewport. |
| **Bottom Inspector (Full Width)** | Column division: **Selected operation** (selected without placeholder), **Properties**, **Validation**, **Stats** (e.g. Nodes / Connections / Outputs counts), **Notes** (free notes). **5 block horizontal strip** as in mockup. |
| **FOOTER ACTION** | Left: **Recompute (dry-run)**, emphasis **Recompute & save graph**. Center: **Last recompute** time, **Graph is valid**, etc. status. Right: **+ Add output**, **Clear canvas** (confirmation dialog for dangerous actions). |

**React Flow implementation notes**

- **Background**, **Controls**, **MiniMap** in `@xyflow/react` (can be included in scope even if there is no minimap in the mockup — MiniMap is optional if mockup is priority).
- Node and edge components share a set of Tailwind classes tailored to the card, port, and curved line styles of the mockup.
- **Intermediate** is shown as a **formal state** between operation blocks like a mock-up, and is expressed without conflict with §3·§7 rules.

---

## 3. Connection rules (UI + server sorting)

Allow (Summary):

- `source shape` → `operation`  
- `intermediate shape` → `operation`  
- `operation` → `intermediate shape`  
- `intermediate shape` → `target shape` (Output node in the document)

prohibition:

- `operation` → `operation`  
- `source` shape → `intermediate` / `target`, etc. Direct connection of the same shape without **delivery**
- `operation` → `target/output` directly
- Connections conflicting with other server topologies

**In implementation**: React Flow `isValidConnection` + double server validation.

---

## 4. Supported Operation Range

Limited to the list specified in the documentation (lowercase snakes will match existing engine keys — e.g. `rotate_cw` vs `ROTATE_CW` canonicalized to a single source in the adapter).

The number of `OPERATION_SPECS` inputs and outputs **must** [`operation_engine`](django_apps/shapez_solver/services/operation_engine.py) / is confirmed by comparing with the existing meta.

---

## 5. File/build suggestions (based on repository)

In document §5, `assets/js/graph_editor/` is recommended in this repository, for example:

```text
assets/js/graph_editor/ # or frontend/graph_editor/
  package.json (Vite)
  vite.config.ts                 # outDir → django_apps/web/static/web/js/
  src/main.tsx
  src/GraphEditorApp.tsx
  ...
django_apps/web/templates/web/
macro_pattern_graph.html # Bundle script one line + root div
django_apps/web/static/web/js/
graph_editor.bundle.js # Build output
```

When using Tailwind: Include the React source path in `@source` to prevent missing purges.

---

## 6. Data model (TypeScript + storage payload)

The TS type of documents §6·§7 ​​is maintained, but **Stored JSON** is moved down to the domain schema (`nodes[].kind` / `role` / `edges[].kind`).

Suggested functions:

- `reactFlowToDomainGraph(rfNodes, rfEdges): graph_document`
- `domainGraphToReactFlow(doc): { nodes, edges }`
- `legacyMountGraphToReactFlow` — Compatibility with current `macro_recipe_graph_visual` output is defined in Phase 1.

---

## 7. Interaction (Sort document §8)

### 7.1 Automatic intermediate upon operation drop

- When adding an operation node, intermediate (shape) nodes are automatically created **as many as the number of output slots** + `operation → intermediate` edges are automatically connected.
- The deletion policy defaults to the document §11 recommendation, but requires **product confirmation** before implementation.

### 7.2 Operation arity

- Multi-input/output is unified with handle·`slot`·server edge `slot` fields.

---

## 8. Color Mixer

- `RGB_COLOR_MIX_TABLE` etc. target **same source** as [`color_mix_semantics`](django_apps/shapez_solver/services/color_mix_semantics.py) and existing rules (synchronized with unit tests in case of frontend duplication).

---

## 9. Step-by-step roadmap (integrated with document §11)

| Phase | focus | output |
|------:|------|--------|
| **1** | WebGL graph and state separation, domain JSON adapter | `legacyToReactFlow` draft, WebGL graph entry inactivity flag |
| **2** | Vite + React Flow Minimum Mount | `GraphEditorApp`, build pipeline, Django page connection |
| **3** | 4 types of custom nodes | Shape / Operation / Intermediate / Output |
| **4** | Edge Verification | `canConnect`, arity, prevent duplicate input |
| **5** | Automatic intermediate creation | Drop·multi output |
| **6** | palette | Catalog Single Source, Search·DnD |
| **7** | Inspector | Node-specific fields·COLOR_MIXER UI |
| **8** | Backend integration | Reflect existing `graph/recompute/` + verification results |
| **9** | automatic placement | 1st column, 2nd Dagre/ELK |
| **10** | WebGL unification | Tile preview non-WebGL, select panel only Three |

---

## 10. Scope of disposal (subject to deletion/reduction during implementation)

Candidates to be organized in Phase 1~2 after approval:

- [`django_apps/web/static/web/js/macro_pattern_graph_editor.js`](django_apps/web/static/web/js/macro_pattern_graph_editor.js) My existing canvas mount path.
- Full mount of the graph at [`macro_pattern_staff_graph.mjs`](django_apps/web/static/web/js/macro_pattern_staff_graph.mjs) (or minified to only be called from React)
- **WebGL/mount code for the graph** tied to the staff page; However, **solver timelines that reuse the same module** are not touched (maintaining [`architecture.mdc`](.cursor/rules/architecture.mdc) boundaries).

---

## 11. Testing (reflecting document §12)

- **Unit**: `canConnect`, arity, auto-intermediate, domain ↔ RF adapter, color table
- **Integration**: Django `POST graph/recompute`, page smoke, save and reload
- **Regression**: Existing `graph_document` load/migration smoke

---

## 12. Risk/Response (Summary of Document §13)

| danger | Response |
|------|------|
| Domain ↔ RF model mismatch | Single adapter module + server verification to the final truth |
| Build/Static Asset Path | Vite outDir · Collectstatic · Cache bursting (`?v=`) specified |
| WebGL context leak | select panel singleton + dispose test |

---

## 13. Recommended first 5 actions (same as document §14)

1. Domain `graph_document` schema and RF model mapping table confirmed
2. Legacy export + `domainGraphToReactFlow` skeleton
3. Mount an empty React Flow canvas on your Django page
4. Only 4 custom node styles
5. `isValidConnection` + status bar message

---

## 14. Approval Gate

- Enter branch implementation after **human approval** of this document or its revised version.
- `[documents/` writing language]: Main text is Korean, identifier, path, and API are kept in the original.

---

## 15. Relationship to previous plans

- [`plan_recipe_graph_workbench_2026-05-04.md`](documents/plan_recipe_graph_workbench_2026-05-04.md) was centered around the **WebGL workbench layout**. Once this document is approved, the UI portion of the plan will be **replaced with the React Flow premise**. Common requirements such as domain, topology, and palette range are inherited.

---

## 16. Final Todo list

Track your progress during implementation with this list. (The order gives priority to phase and dependency relationships.)

### Common · Preparation

- [ ] This document **person approval** record (approval date/summary)
- [x] `graph_document` ↔ React Flow **mapping table** documentation (PR or appendix to this document)
- [x] Vite (or optional builder) + React + `@xyflow/react` **Project Scaffolding**
- [x] Build output → `django_apps/web/static/web/js/` and templates **bundle load·cache burst**
- [x] Tailwind: React source path `@source` registration and purge verification

### Phase 1 — Domain State Separation · Adapter

- [x] staff graph related **WebGL/mount entry point** file list confirmed
- [x] Extract **serializable graph snapshot** (based on domain JSON)
- [x] `domain_graph_to_react_flow` / `react_flow_to_domain_graph` **Skeleton + unit test draft**
- [x] Define **compatibility scope** with legacy visualization output (`macro_recipe_graph_visual`, etc.)
- [x] Add **inactive flag** (or feature flag) to existing WebGL graph

### Phase 2 — React Flow minimum installation · §2.1 Layout framework

- [x] Mount **React root + bundle** on `macro_pattern_graph.html` (or dedicated template)
- [x] `GraphEditorApp` / `ReactFlowProvider` **Default configuration**
- [x] **Page grid** aligned with §2.1: header, left palette area, central canvas, bottom 5-column inspector, footer (placeholders allowed)
- [x] Background · pan/zoom · selection operation
- [x] (optional) Controls · MiniMap

### Phase 3 — 4 types of custom nodes

- [x] `ShapeNode` — Source material/mini-preview (no WebGL)
- [x] `OperationNode` — icon, label, ID, input/output handle
- [x] `IntermediateNode` — produced-by · Mini preview
- [x] `OutputNode` — Target·Right OUTPUTS zone placement policy reflected
- [x] Selection/Warning/Error **Badge Style** (Mockup Tone)

### Phase 4 — Edge/Connection Verification

- [x] Custom `RecipeEdge` (Bezier · `data.domainKind`-specific stroke) — `frontend/recipe_graph_editor/src/recipeFlowEdges.tsx`
- [x] `isValidConnection` — §3 rule + `recipeConnection.ts`·`wouldConnectAfterRemovals`
- [x] Block Operation **input arity**·**duplicate input** — `operationArity.ts`, etc.
- [x] Message on bad connection — `#macro-graph-status` (throttle) + bottom **Inspector Validation** column (`GraphEditorApp.tsx`)
- [x] §3 **intermediate → output(target)** Manual wiring — edge type ``delivery`` (`recipe_graph_topology.py`·`recipe_graph_recompute.py`·RF adapter·`recipeConnection.ts`)

### Phase 5 — Automatic Intermediate

- [x] Calculate in the palette **When dropped**, automatically create intermediate + edges as many as the number of operation nodes + outputs — Canvas `onDrop` + `ensureOperationOutputArtifacts` (Click to add is staged after placing and connecting the grid as before)
- [x] Multi-output operations **per-slot intermediate** and position offsets — `operationOutputStaging.ts`, etc.
- [x] Implement and check **intermediate·edge cleanup policy** when deleting nodes/operations — `recipeGraphNodeCleanup.ts` + `GraphEditorApp` `onNodesChange` (removes output staging intermediate chain when deleting operations)

### Phase 6 — Operation Palette

- [x] `operationCatalog`(SHAPE / ROTATE / CUT / FLOW / COLOR) — **Single registration with engine list** (bootstrap + inactivity handling)
- [x] Search·Category·Icon+Label card
- [x] Drag-and-drop · Additional keyboard-accessible buttons — Operations · Empty source **DnD**(`RecipeFlowBoard`); Palette items retain **Enter/Space** click action with `<button>`
- [x] Check LOGIC·UTILITY **not exposed** (specify catalog filter policy) — `operationPaletteGroups.ts` comment: Non-displayed series are inactive if they do not include a catalog or do not include `engineOperationIds`

### Phase 7 — Inspector Panel

- [x] Edit **Properties** dedicated field for each selected node — Inline form (`InspectorNodeProperties`) in bottom Properties column when single selected; Existing summary text when multiple/unselected
- [x] **Validation** panel — Server `validationOk`/footer hint + **Connection refused message** Summary
- [x] **Stats** — Number of nodes, edges, and outputs
- [x] **Notes** — browser `localStorage`(`shapez-recipe-graph-notes:<recipeId>`), 400ms debounce save; Server unsynchronized

### Phase 8 — Backend integration

- [x] `POST … /graph/recompute/` **dry-run** Connection and UI reflection (button + silent dry-run after connection)
- [x] **Save(commit)** Flow and error handling
- [x] Update **intermediate shape_code·verification status** with recalculation results (synchronize response `react_flow`)
- [x] Reflection of node/edge **validationState** when backend validation fails (partially done if not propagated to RF node data) — node `data.validationSeverity` (mapping `node_ids` of issues); Edge display not implemented

### Phase 9 — Automatic Deployment

- [x] **Auto arrange** button — Primary left → right column layout — `recipeGraphAutoLayout.ts` + Canvas toolbar **Auto arrange**
- Validate **position saved** after manual dragging [x] — adapter fractional coordinates round-trip unit test (`test_react_flow_round_trip_preserves_fractional_positions`)
- [ ] (2nd) Determination and integration of Dagre/ELK

### Phase 10 — WebGL Preview Unification

- [x] Graph Tiles **Remove WebGL** — React Flow editor bundle (`frontend/recipe_graph_editor`) has node mini-previews based on images/CSS (without Three/WebGL); The legacy staff WebGL path is in the Phase「Disposal/Cleanup」 item.
- [ ] Reuse Three.js / GLTF **single renderer** only for **selected nodes** panel
- [ ] Enlarged modal checks **creation when mount and dispose** pattern when closing

### Disposal · Cleanup

- [x] Staff only **Sphere Graph WebGL Mount** — Default is RF (`config/settings.py`: if not set, `RECIPE_GRAPH_USE_REACT_FLOW=True`); Legacy is loaded into branch [`macro_pattern_graph.html`](django_apps/web/templates/web/macro_pattern_graph.html) only when `RECIPE_GRAPH_USE_REACT_FLOW=0`
- [ ] Solver timeline, etc. **Shared module regression** test passed confirmation

### Tests · QA

- [ ] Unit: adapter·`canConnect`·arity·auto-intermediate·color table
- [ ] Integration: Page load·recompute·save·reload·§2.1 Smoke (palette·canvas·inspector visibility)
- [ ] Regression: Load/migrate existing `graph_document`

### Document · Finalization

- [x] [`recipe_graph_editor_progress`](documents/recipe_graph_editor_progress_2026-05-04.md) — Reflection of subsequent sections such as React Flow transition and delivery edge (2026-05-04 change history)
- [x] `structure.md` — One line for **`frontend/recipe_graph_editor/`** source and **`static/web/js/recipe_graph_editor/`** output path.

---

## 17. Appendix A — `graph_document` ↔ React Flow Snapshot Mapping (v1)

> Implementation authority: `domain_graph_to_react_flow` / `react_flow_to_domain_graph` in `django_apps/shapez_solver/services/recipe_graph_react_flow_adapter.py`. The snapshot top-level `version` field is `REACT_FLOW_GRAPH_PAYLOAD_VERSION` (currently 1). The graph storage contract (`schema_version`, `nodes`, `edges`) is maintained by `graph_document`.

### 17.1 Node

| `graph_document` | React Flow `type` | `data` (summary) |
|------------------|-------------------|---------------|
| `kind: "shape"`, `role: "source"` | `shape` | `shape_code`, `quantity`, `role` |
| `kind: "shape"`, `role: "intermediate"` | `intermediate` | Same |
| `kind: "shape"`, `role: "target"` | `output` | Same |
| `kind: "operation"` | `operation` | `operation`, (optional) `paint_color` |

Common: `id`, `position: { x, y }` ← `x`, `y` (float) in the domain.

### 17.2 Edge

| `graph_document` | React Flow |
|------------------|------------|
| `from`, `to`, `kind` (`input` \| `output` \| `delivery`) | `source`=`from`, `target`=`to`, `data.domainKind`=`kind` (`delivery`: intermediate→target delivery) |
| (optional) `slot` | `data.slot` |

React Flow `id` is given by the `e-{from}-{to}-{kind}` rule in the snapshot.

### 17.3 Bootstrap · Recalculation API

- The `react_flow_initial` key is included in the `macro-graph-bootstrap` JSON of the staff graph page (`macro_pattern_graph`). The value is the conversion result of a verified `graph_document`, or `null` if there is no document or validation fails.
- `POST … /api/recipes/<pk>/graph/recompute/` The request body sends **only one of `graph_document` and `react_flow`**. When sending `react_flow`, the client does not reverse convert (TypeScript), but the server processes it in the following order: `react_flow_to_domain_graph` → `validate_graph_document` → `recompute_graph_document` (Authority: Python adapter only).
- The response JSON always contains an updated **`react_flow`** snapshot (`domain_graph_to_react_flow(doc)`), and the editor synchronizes the canvas state with this value.

### 17.4 Legacy WebGL/Graph Mount Entry Point (to be cleaned up)

| Path | Role |
|------|------|
| `django_apps/web/static/web/js/macro_pattern_graph_editor.js` | staff Macro Graph Legacy Editor (Card·Canvas·Three importmap linked) |
| `django_apps/web/static/web/js/macro_pattern_staff_graph.mjs` | Graph visualization module exclusively for staff |
| `django_apps/web/static/web/js/solver_timeline.js` + `solver_timeline/graph_mount.js` | Mount graph with `mountGraph` in solver timeline |

After switching to React Flow, the **graph editing** path above is blocked and removed with a flag, and **read-only** shared modules such as the timeline are protected through regression testing.

### Compatible with 17.5 `macro_recipe_graph_visual`

The `visual_graph` created by `serialize_macro_recipe_visual` is preserved as a **read-only** summary for catalog/API responses. The authority of the editor state is `graph_document` and the React Flow snapshot in this appendix, and the number and ID of visual nodes for the same recipe do not need to be 1:1 (the editor follows the `recipe_graph_react_flow_adapter` schema).
