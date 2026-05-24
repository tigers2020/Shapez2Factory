# Weekly plan: atomic sprite atlas + Canvas2D composited preview

**Role · perspective**: Rendering Pipeline Architect  
**Status**: Draft to fix this week's (2026-05-06 week) direction — review · approval recommended before implementation  
**Related prior plan**: [plan_deferred_png_warm_queue.md](plan_deferred_png_warm_queue.md) (deferred warm · `sync_png=False`)

---

## One-line conclusion

**Drop the pattern of baking finished shape PNGs per node on the server; pre-generate offline/batch only a finite set of atomic parts (mesh×color×quadrant, etc.), then at runtime use `preview_scene.cells[]` directly as a Canvas2D `drawImage` command buffer.**

---

## Current pipeline and cost

```text
target shape
  → preview_scene generation
  → Playwright
  → Chromium / Three.js
  → offscreen render
  → PNG save
```

Running this path **per node** costs roughly:

```text
O(node count × full_scene_render_cost)
```

Easily hits **request time limits** on Render · Gunicorn · proxy.

---

## Target architecture

### Paradigm shift

```text
full scene server rendering
  → client-side deterministic composition
```

shapez2Factory's `preview_scene.cells[]` already has **raw descriptors** like `mesh_key`, `color_code`, `quadrant_index`, `position` — close to a **render command buffer**. Add:

```text
preview_scene → Canvas2D renderer (client)
```

### Domain assumption (finite sprites)

Example base meshes:

- `default_rect`, `default_circle`, `default_star`, `default_diamond`, `default_pin`, crystal, etc. (aligned with `MODEL_FILES` in [`shape_gltf/constants.js`](../../django_apps/web/static/web/js/shape_gltf/constants.js))

Game color palette is **finite** → entire combination space collapses to **finite sprite atlas**.

---

## Server · assets

### Phase 1 goal

- **Pre-generate ~160 atomic PNGs** (e.g. form×color×`quadrant` q0–q3) via **build · management script**
- Storage candidates:
  - **Single `atlas.png` + `manifest.json`** (UV: `[x,y,w,h]` recommended — fewer HTTP requests · decode cost)
  - Or DB Blob + GET (when ops · version consistency priority; atlas can be one DB row)

### Parts generation script (this week's deliverable)

- Via existing [`scripts/render_graph_preview.mjs`](../../scripts/render_graph_preview.mjs) or **offline-only** script with same Three · camera basis:
  - Render each atomic combo · quadrant only → fixed tile PNG or atlas packing
- Outputs: `atlas.png`, `manifest.json` (key rule e.g. `rect_red_q0`), optional meta (`version`, render preset)

---

## Frontend

- **Tile preview**: **Canvas2D only**, no WebGL N contexts

```text
for each cell in preview_scene.cells:
    key = f(mesh_key, color variant, quadrant, …)
    drawImage(atlas, sx,sy,sw,sh, dx,dy,dw,dh)
```

- As node count grows, cost scales roughly with **draw call count** → near UI level.

---

## Phased strategy (strongly recommended order)

| Phase | Content |
|-------|---------|
| **1** | **Keep warm queue · existing API** — safety net for unregistered keys · fluid · crystal exceptions · quality fallback |
| **2** | **Tile preview only** replace with Canvas2D sprite composition ([`recipeShapePreview.tsx`](../../frontend/recipe_graph_editor/src/recipeShapePreview.tsx) tile branch) |
| **3** | **Shrink Playwright PNG** to modal · export · high-quality only |

---

## Performance comparison (concept)

**Current (composite PNG per node)**:

```text
Node.js → Playwright → Chromium → Three/WebGL → PNG encode → save
```

**After change (tile)**:


```text
drawImage() × cell count
```

---

## Risks · notes

- `transform_key`, fluid carrier, crystal shading may push **atomic set beyond 160** → confirm by enumeration · tests; keep warm/modal for uncovered cases
- Decide whether staff tiles must **pixel-match Playwright** or **approximate preview** policy
- On atlas version bump, **cache invalidation** (filename hash or `manifest.version`)

---

## This week candidate tasks (checklist)

1. **Document atomic key spec**: `mesh_key` × color × quadrant × (optional `transform`) → string key rule
2. **`scripts/` offline build script**: output atlas + manifest (run locally/CI)
3. Decide **static serve or DB load** and pick Django `collectstatic`/migration
4. **Prototype**: Canvas2D composition component for single `preview_scene` + wire tile path
5. **Regression**: golden snapshot or visual smoke for representative cell combos

---

## Reference code paths

- Scene serialization: [`django_apps/shapez_solver/view_graph_serialization.py`](../../django_apps/shapez_solver/view_graph_serialization.py)
- Tile/modal preview UI: [`frontend/recipe_graph_editor/src/recipeShapePreview.tsx`](../../frontend/recipe_graph_editor/src/recipeShapePreview.tsx)
- Existing server PNG render: [`django_apps/web/services/graph_preview.py`](../../django_apps/web/services/graph_preview.py)

---

## Final judgment (architect summary)

This is not a simple timeout workaround but a **structural shift of rendering responsibility from full server scene render to client deterministic composition**. Aligns well with existing `preview_scene.cells[]` model.
