# Recipe Graph Workbench — Execution Plan (2026-05-04)

This document staff The plan is to **completely redesign the layout** of the macro **graph editor** to the attached mockup level and gradually reflect the connection rules, COLOR_MIXER, and verification UX.
(The `graph_document` schema·domain boundary follows the existing [AGENTS.md](../../../../AGENTS.md)·[`architecture.mdc`](../../../../.cursor/rules/architecture.mdc).)

---

## 1. Summary of goals

| axis | Content |
|----|------|
| **UI** | Full redesign (header, palette, canvas, bottom inspector, footer) tailored to the **§2 mockup layout** below. |
| **Domain** | `shape → operation → intermediate(shape) → … → force target` topology; `operation → operation`, etc. is prohibited. |
| **Palette** | Only operations supported by the engine are exposed (SHAPE / ROTATE / CUT / FLOW / COLOR). The LOGIC·UTILITY of the mock-up is **not exposed** (before design). |
| **Color** | Room for `ColorMode` extension to mix existing channel characters; Table-based validation. |

---

## 2. Alignment with layout mockup (based on attached image)

When completely redesigning, **the following area is the primary target**. (Not pixel-by-pixel replication, but **area, role, and information layer** are the same.)

### 2.1 Header (top bar)

- One line of meta, such as app/page title (e.g. Staff · Graph editor), recipe code · name, etc.
- Right actions: **Catalog**, **Edit metadata** (maintain existing URL).

### 2.2 Main break — 2 rows (left palette | right canvas)

**Left: Operations / Node palette**

- Enter **Search** at the top (label/operation key filter).
- Collapse/Title by Category: Actual data only shows **§4 palette range**. (The names of the mock-up, such as BASIC/TRANSFORM/LOGIC, are for reference only, and the implementation is SHAPE·ROTATE·CUT·FLOW·COLOR fixed.)
- Each item: **Icon + Label** Horizontal card, draggable.
- (Optional) Bottom Quick access / Favorites area.

**Right: Canvas Workspace**

- Retains **background grid** and existing pan/zoom behavior.
- Canvas **top toolbar**: Grid toggle, (if available) Snap, Zoom % / ± / **Fit to screen**, etc. — Steps introduced in conjunction with existing `graph_viewport`.
- **Minimap**: Overlay on top right of canvas (small overall map); Due to the difficulty of implementation, it is placed as **Phase lower priority**, but **place (placeholder)** can be secured in the layout.

### 2.3 Bottom — Inspector/Status Panel (full width)

Place the following blocks in a **line or collapsible strip** as shown in the mockup.

| block | Role |
|------|------|
| Node Info | Select node name, type, short description, and preview (if available). |
| Properties | Editing by node (dropdown, number, etc.) — Migrate existing editing modal contents step by step. |
| Validation | Recalculation/verification messages, success, warning, error. |
| Stats | Number of nodes, number of edges, (optional) number of warnings/errors, etc. |
| Notes | User memo (optional, whether to link with recipe field to be determined separately). |

### 2.4 Bottom — Action Bar

- **Recompute (dry-run)**, **Recompute & save graph**.
- One line of status: last recalculation time, validity, etc.
- **Add node / Add operation / Delete selected**, etc. — Integration with existing CRUD toolbar.

### 2.5 Implementation Files (Expected)

- Template: [`django_apps/web/templates/web/macro_pattern_graph.html`](../../../../django_apps/web/templates/web/macro_pattern_graph.html) — Grid shell/area id.
- Script: [`django_apps/web/static/web/js/macro_pattern_graph_editor.js`](../../../../django_apps/web/static/web/js/macro_pattern_graph_editor.js) — Break down the huge `innerHTML` into section-by-section builders.
- Style: Maintain Tailwind; Small auxiliary or scoped blocks within `web/static/web/css` templates when needed.

---

## 4. Operations to be exposed to palette (engine matching)

Logic·Utility, etc. drawn in the mock-up are **excluded at this stage**.

- **SHAPE**: Base shape  
- **ROTATE**: `rotate_cw`, `rotate_ccw`, `rotate_180`  
- **CUT**: `cutter`, `cutter_full`, `half_destroyer`, `splitter`  
- **FLOW**: `stacker`, `swapper`, `pin_pusher`  
- **COLOR**: `painter`, `color_mixer`  

The icon uses a static URL from the existing [`catalog_operations_payload`](../../../../django_apps/shapez_solver/services/macro_recipe_staff_catalog.py).

---

## 5. Domain/Verification (Phase 1)

- Server: Add **topology verification** after `validate_graph_document` (whether `to` of output edge is intermediate shape, input comes only from shape, etc.).
- Client: **Connection refused** + message with same rule in `recipeWireConnect`.
- Unit tests: allow/deny cases.

---

## 6. Color Mixer (Phase 3)

- [`color_mix_semantics.py`](../../../../django_apps/shapez_solver/services/color_mix_semantics.py) extension and `ColorMode` placeholder.
- Allowed combinations reflected in Inspector Properties (dropdown/warning).

---

## 7. Canvas Advanced UX (Phase 4)

- Visual differentiation by node role ([`graph_markup.js`](../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js)).
- Violation edge style (dotted/colored) — Server verification result or client estimate.
- Minimap/wire color level — by priority.

---

## 8. Documentation/Approval/Verification

- This plan follows the Korean text rules of `documents/`.
- Approval gate before implementation follows project [protocols/README.md](../../../../protocols/README.md).
- Verification: `pytest`(unit·integration), change section lint.

---

## 9. Priorities in this plan

1. **Full layout redesign (§2)** — Reflecting user requests, separating the same areas as the mock-up.
2. **Topology Verification (§5)** — Avoiding bad graphs.
3. Color Mixer·Inspector details.
4. Additional features such as permanent storage of minimap, Fit, and Notes.
