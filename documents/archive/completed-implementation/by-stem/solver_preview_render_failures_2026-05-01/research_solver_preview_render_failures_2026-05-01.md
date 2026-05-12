# Solver Preview Render Failures Research

## Scope

- Reproduced on `http://127.0.0.1:8000/solver/?code=CuRuSuWu`
- Symptom: many graph-node previews fail to display while a few still render
- Focused on the solver graph frontend and the preview payload path

## What I checked

### 1. Solver graph payload path

- `django_apps/shapez_solver/views.py`
  - `_serialize_graph_node()` includes `preview_scene` for every shape node
  - `_build_preview_scene()` derives the same canonical `ShapeRenderScene` used elsewhere
- Result: the backend is already providing preview data per node

### 2. Graph preview mounting path

- `django_apps/web/static/web/js/solver_timeline.js`
  - `mountGraphShapePreviews()` loops all `[data-graph-shape-preview]`
  - each node calls `await mountShapeGltfViewer(viewer)`
- `django_apps/web/static/web/js/shape_gltf_viewer.js`
  - `mountViewer()` creates a fresh `THREE.WebGLRenderer`
  - every graph node therefore owns a separate WebGL context

### 3. Reproduction evidence

- The reproduced graph contains many preview nodes at once
- The failure pattern is partial, not deterministic by shape type:
  - some nodes render
  - many later nodes appear blank
- This does **not** match a parser failure or missing `preview_scene`
- This **does** match browser/WebGL context exhaustion behavior when many independent renderers are mounted in one page

## Working diagnosis

The current graph UI mounts one interactive Three.js viewer per shape node. On dense solver graphs this creates too many WebGL renderers at once, and browser rendering becomes unreliable. The data is present, but the chosen rendering surface is too heavy for graph-scale fanout.

## Why this is likely the right root cause

- Graph nodes render through `shape_gltf_viewer.js`, not through static HTML/SVG
- `mountViewer()` always creates a new `WebGLRenderer`
- Dense solver graphs can easily create dozens of viewers
- The live preview panel still tends to work because it mounts only one viewer
- The selected-node detail panel should also remain safe because it mounts only one viewer

## Candidate fix directions

### Option A. Keep WebGL everywhere and try to pool/reuse contexts

- Pros:
  - preserves 3D interaction in every node
- Cons:
  - much more complex lifecycle/state management
  - still heavy for large graphs
  - higher risk for regressions and leaks

### Option B. Replace graph tiles with lightweight 2D previews

- Pros:
  - removes graph-scale context pressure
  - simplest reliability fix
- Cons:
  - does not preserve the current glTF/WebGL look
  - visual quality drops relative to the current 3D thumbnails

### Option C. Server-side glTF prerender to image snapshots for graph tiles

- Pros:
  - keeps graph tiles visually close to the current 3D preview
  - removes client-side WebGL fanout from dense graphs
  - still allows the main live preview and selected-node detail to remain interactive
- Cons:
  - requires a backend render pipeline and image transport strategy
  - introduces caching / invalidation and media generation concerns

## Recommended direction

Option C.

Use backend prerendered image thumbnails for solver graph tiles and keep `shape_gltf_viewer.js` only for:

- the main live preview panel
- the selected-node detail panel

This keeps the graph stable under load while preserving the current 3D-like thumbnail quality much better than a 2D SVG replacement.
