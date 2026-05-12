# Solver Preview Render Failures Plan

## Goal

Make solver graph shape previews render reliably for dense graphs such as `CuRuSuWu` by removing the graph view's dependence on one WebGL renderer per node, while preserving the existing glTF thumbnail look as closely as practical.

## Proposed change

Replace graph-node preview mounting from per-node Three.js viewers to backend-generated prerendered PNG thumbnails derived from the same glTF visual pipeline, while leaving the following surfaces unchanged:

- solver page live preview panel: keep Three.js glTF viewer
- selected-node detail panel: keep Three.js glTF viewer

## Implementation outline

### 1. Add a backend graph-thumbnail renderer

- Add a web-layer service that can produce a PNG thumbnail from canonical preview data
- Input should remain `ShapeRenderScene` or equivalent canonical preview payload
- Output should be a stable image representation usable in graph tiles
- Keep the rendering adapter at the web layer so domain/application stay renderer-neutral

### 2. Decide transport format for prerendered images

- Preferred first pass: embed as data URL in the graph payload to avoid file lifecycle complexity
- Secondary option if payload size becomes too large: cache generated images and return stable media URLs
- The first implementation should bias for correctness and simplicity over perfect network efficiency

### 3. Serialize graph shape nodes with prerendered image data

- Update `django_apps/shapez_solver/views.py`
- For shape nodes, add a graph-tile image field such as `preview_image_url`
- Preserve existing `preview_scene` because the selected-node detail still needs interactive WebGL

### 4. Change solver graph tile markup to use `<img>` instead of auto-mounted WebGL

- Update `django_apps/web/static/web/js/solver_timeline.js`
- In `renderShapeGraphNode()`, render the server-provided prerendered thumbnail
- Remove graph-tile calls to `mountShapeGltfViewer()`
- Keep `renderSelectedNodeDetail()` using `mountShapeGltfViewer()`

### 5. Add regression coverage

- Add tests for thumbnail serialization on solver graph nodes
- Add tests for the backend thumbnail renderer at least at the contract level
- Add a web test that confirms graph markup uses prerendered images rather than mounting per-node viewers

## Tradeoffs

- Graph tiles become non-interactive previews
- Focused inspection remains interactive in the selected-node detail panel
- Reliability improves significantly for larger graphs
- Response size and/or server render cost will increase compared with plain JSON scene data

## Validation plan

- Manual:
  - open `/solver/?code=CuRuSuWu`
  - confirm all graph shape nodes show a visible preview
  - confirm graph tiles are rendered from prerendered images rather than live per-node WebGL mounts
  - confirm selected-node detail still shows interactive 3D viewer
- Harness:
  - `pytest`
  - `ruff check .`
  - `mypy .`
  - `black .`

## Risks

- The backend thumbnail pipeline may need Node/Three.js or another headless rendering path to stay visually aligned with the current glTF result
- Data-URL payloads may become large for very dense graphs
- If backend prerender depends on assets or runtime assumptions that differ from the browser viewer, visual mismatches may appear
