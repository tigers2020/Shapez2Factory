# Plan: graph preview SVG cleanup (2026-05-02)

Related research: [documents/research_graph_preview_svg_cleanup_2026-05-02.md](./research_graph_preview_svg_cleanup_2026-05-02.md)

Original request summary: remove all dead SVG-related code left in graph preview fallback; keep PNG-based path only.

## Implementation approach

1. Delete lightweight SVG renderer, SVG helpers, and `markup`-based fallback from [django_apps/web/services/graph_preview.py](../../../../../django_apps/web/services/graph_preview.py).
2. Shrink PNG renderer to simple result: `image_url` on success, `image_url=None` and `alt_text` only on failure.
3. Remove `preview_markup` field from [django_apps/shapez_solver/view_serialization.py](../../../../../django_apps/shapez_solver/view_serialization.py).
4. Simplify [django_apps/web/static/web/js/solver_timeline/graph_markup.js](../../../../../django_apps/web/static/web/js/solver_timeline/graph_markup.js) to image-only rendering; text fallback only when image absent.
5. Update graph preview/unit/integration tests: remove SVG selection and markup expectations; verify PNG/no-image paths.

## Compatibility criteria

- Solver graph nodes must still provide `preview_image_url` and `preview_alt`.
- Preserve PNG cache hit path and cache URL structure.
- On preview generation failure, API/page must not break and show "No preview" fallback.

## Verification

- `python -m pytest tests/unit/web/test_graph_preview.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest`
- `python -m ruff check .`
- `python -m mypy .`
- `python -m black .`
