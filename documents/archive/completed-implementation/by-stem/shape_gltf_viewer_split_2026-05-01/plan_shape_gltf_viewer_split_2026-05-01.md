# Plan: shape_gltf_viewer split (2026-05-01)

Related research: [documents/research_shape_gltf_viewer_split_2026-05-01.md](./research_shape_gltf_viewer_split_2026-05-01.md)

Original request summary: split [django_apps/web/static/web/js/shape_gltf_viewer.js](../../../../../django_apps/web/static/web/js/shape_gltf_viewer.js) into responsibility-based ES modules while keeping public API `mountShapeGltfViewer` / `disposeShapeGltfViewer` and auto-mount on the existing entrypoint for compatibility.

## Scope

- Create folder [django_apps/web/static/web/js/shape_gltf/](../../../../../django_apps/web/static/web/js/shape_gltf/).
- Sequentially extract constants, loader, materials, transform, transitions, renderer, render_scene, ui_modes from `shape_gltf_viewer.js`.
- Leave entrypoint as thin facade: imports, `viewerStates` WeakMap, `mountShapeGltfViewer`, `disposeShapeGltfViewer`, auto-mount loop only.

## Implementation approach

1. Extract `constants.js`, `model_loader.js`, `materials.js` first for data/loading/material responsibilities.
2. Extract `transform.js`, `transitions.js` for position math and animation interpolation.
3. Extract `renderer.js`, `render_scene.js`, `ui_modes.js` for scene assembly and UI event wiring.
4. Finally shrink [django_apps/web/static/web/js/shape_gltf_viewer.js](../../../../../django_apps/web/static/web/js/shape_gltf_viewer.js) to facade form.

## Compatibility criteria

- `import "./shape_gltf_viewer.js"` and `import { mountShapeGltfViewer, disposeShapeGltfViewer } from "./shape_gltf_viewer.js"` must keep working.
- Auto-mount via `data-shape-gltf-viewer` + `data-shape-gltf-auto-mount` must run at same timing as before.
- Preserve render output, mode switches (`original`, `layer`, `quadrant`), and dispose behavior without visual spec change.

## Verification

- Verify smoke via `pytest`; at minimum [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py) static asset references must pass.
- Manually verify viewer mount, mode switch, dispose on demo page when possible.
- Even for JS-focused change, final report must note unrun verification and remaining risks per repo rules.

## Out of scope

- Do not edit `vendor/three`.
- No new view modes, constant tuning, or visual redesign.
