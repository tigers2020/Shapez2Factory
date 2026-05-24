# graph_preview.py refactoring plan

Date: 2026-05-02

## Goals

- Simplify single large renderer in `graph_preview.py` into internal helper composition.
- Preserve public contract and behavior.
- Do not add SVG-related code.

## Change scope

- `django_apps/web/services/graph_preview.py`
- `tests/unit/web/test_graph_preview.py` if needed

## Approach

1. Add internal target helper bundling cache key, cache path, image url, alt text.
2. Add internal cache helper for PNG cache lookup and validity checks.
3. Add internal prerender helper for scene file write and `node render_graph_preview.mjs` invocation.
4. Leave `PlaywrightPngGraphPreviewRenderer.render()` as orchestration only.
5. Run existing tests to verify contract preservation.

## Expected benefits

- Clearer responsibility boundaries when reading the file.
- Easier cache policy or prerender strategy changes later.
- Easier to trace failure fallback behavior.
