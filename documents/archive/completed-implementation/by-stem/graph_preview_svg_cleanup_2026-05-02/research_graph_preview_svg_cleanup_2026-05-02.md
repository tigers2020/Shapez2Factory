# graph preview SVG cleanup research (2026-05-02)

- User request: treat SVG-related code as dead and delete all of it.
- SVG path core is `LightweightGraphPreviewRenderer` and `_render_scene_markup()` helpers in [django_apps/web/services/graph_preview.py](../../../../../django_apps/web/services/graph_preview.py).
- [config/settings.py](../../../../../config/settings.py) default is already `SOLVER_GRAPH_PREVIEW_RENDERER = "playwright_png"`. Runtime default is PNG preview; SVG remains only as fallback/selection mode.
- [django_apps/shapez_solver/view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py) sends `preview_markup`, `preview_image_url`, `preview_alt` together on graph shape node payload.
- Frontend [django_apps/web/static/web/js/solver_timeline/graph_markup.js](../../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js) uses `node.preview_markup || "No preview"` fallback; SVG markup payload still consumed directly.
- Tests: [tests/unit/web/test_graph_preview.py](../../../../../tests/unit/web/test_graph_preview.py) verifies lightweight renderer selection and SVG markup output; [tests/integration/web/test_web_smoke.py](../../../../../tests/integration/web/test_web_smoke.py) verifies `preview_markup` string presence.
- SVG deletion scope is three bundles:
  1. backend renderer: delete lightweight SVG renderer and related helpers
  2. API serialization: remove `preview_markup` field
  3. frontend/tests: remove markup fallback; update to image/no-preview criteria
- `PlaywrightPngGraphPreviewRenderer` currently falls back to lightweight renderer on PNG failure. Natural replacement after SVG removal: empty preview with `image_url=None` on failure.
- `graph_preview_cache` URL and PNG cache key path are SVG-agnostic and can stay.
