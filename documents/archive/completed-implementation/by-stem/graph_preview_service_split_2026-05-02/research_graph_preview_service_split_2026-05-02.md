# graph_preview.py research

Date: 2026-05-02

## Targets

- `django_apps/web/services/graph_preview.py`
- `tests/unit/web/test_graph_preview.py`
- `django_apps/shapez_solver/view_graph_serialization.py`

## Current observations

- Public contract today: `GraphPreview`, `GraphPreviewRenderer`, `get_graph_preview_renderer()`, `PlaywrightPngGraphPreviewRenderer`.
- SVG fallback already removed; PNG generation is the only official path.
- One `PlaywrightPngGraphPreviewRenderer` class owns:
  - cache key calculation
  - cache path/URL assembly
  - PNG validity check
  - temporary scene json file creation
  - `node render_graph_preview.mjs` subprocess call
  - failure generation disable flag management
- `view_graph_serialization.py` consumes this renderer via protocol; internal split is safe if public contract preserved.

## Test criteria

- Default renderer selection must be PNG renderer.
- Cache key must be stable/versioned.
- On prerender failure, fallback must be `image_url is None`.
- Valid cached PNG must be reused.

## Refactoring points

- Splitting cache and subprocess into separate helpers shortens orchestration.
- `render()` should read only:
  1. render target calculation
  2. cache hit check
  3. generation disabled check
  4. PNG generation attempt
  5. failure fallback
- Safer to keep public import path and expected method `cache_key()`.

## Cautions

- Per user request, do not revive dead SVG code.
- Tests use subclass override `_invoke_playwright_prerender()`; keep that override point.
