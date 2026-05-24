# Plan: staff macro graph PNG deferred generation + client warming queue

**Status**: implement after approval  
**Written**: architecture review reflected (2026-05-06)

---

## One-line conclusion

**Do not create PNGs with Playwright during HTML/API serialization (cache hits only); browser sequentially calls warm API with concurrency 1 to generate one missing preview at a time.**

---

## Background

| Before | After |
|--------|-------|
| Render all shape node PNGs on one page request | Page request cache lookup only → fast response |
| Continuous Playwright → Gunicorn timeout · OOM risk | Warming: one HTTP per node → one Playwright per request |

**Constraint**: `GET /internal/graph-preview-cache/<hash>.png` alone cannot restore `preview_scene`, so **do not put PNG generation on image GET handler on miss.**

---

## Design

### 1) Serialization: `sync_png` (name fixed)

Add flag to [`serialize_graph_node`](django_apps/shapez_solver/view_graph_serialization.py).

| `sync_png` | Behavior |
|------------|----------|
| `True` (default, backward compatible) | Same as today: Playwright on cache miss |
| `False` | **cache hit**: return `preview_image_url` · `preview_alt` / **cache miss**: **no PNG generation** |

**Extra fields on node payload on cache miss** (staff macro graph · warming client contract):

- `preview_cache_key`: string (same as renderer cache_key; for warm request id)
- `needs_warm`: `true`
- `preview_scene`: same as today (client can POST in warm body)

Optional: prefill `preview_alt` when possible without `preview_scene` for accessibility.

### 2) Renderer: cache-only lookup

[`PlaywrightPngGraphPreviewRenderer`](django_apps/web/services/graph_preview.py): function that returns `GraphPreview` from DB/filestore **without generation** (e.g. `render_cached_only`).  
Document `NoopGraphPreviewRenderer` always miss or `image_url=None` policy.

### 3) Staff HTML view

[`macro_pattern_graph`](django_apps/web/views.py): propagate **`sync_png=False`** on `serialize_recipe` / `serialize_macro_recipe_visual` path (add option on `macro_recipe_graph_visual` / `view_graph_serialization` signatures).

**Keep** existing `enrich` `visual_graph` reuse.

### 4) Warm API

- **Method/Path**: `POST` (proposed) `/internal/staff/macro-patterns/api/graph-preview/warm/`  
- **Auth**: `staff_site_required` + CSRF (session cookie POST)
- **Phase 1 payload** (simple impl):

  ```json
  {
    "cache_key": "24-char hex...",
    "preview_scene": { }
  }
  ```

  Server: verify `cache_key` **matches** `preview_scene` hash (400 on mismatch) → one `render()` → DB/disk save.

- **Response** (keep existing URL scheme, Django `reverse` basis, not `/media/...`):

  ```json
  {
    "ok": true,
    "cache_key": "...",
    "preview_image_url": "/internal/graph-preview-cache/....png"
  }
  ```

- **No generation attempt on GET cache URL** (already agreed).

### 5) (Optional · phase 2) Payload shrink: server-side scene temp store

When many nodes, repeating `preview_scene` in HTML can be large.

- **Final form**: on serialize server stores `preview_cache_key → preview_scene` in short TTL cache (e.g. Django cache framework / Redis / DB aux table); HTML sends **`preview_cache_key` + `needs_warm` only**.
- **Warm API body**: `{ "cache_key": "..." }` only → server loads scene from cache then `render()`.

Initial impl starts with **`preview_scene` in body**; split to phase 2 if needed.

### 6) Frontend

- After macro graph editor mount: collect nodes with `needs_warm === true`.
- Sequential `fetch` with **concurrency 1** (include `X-CSRFToken`).
- On success set node `data.preview_image_url`, remove `needs_warm` (React Flow `setNodes`, etc.).
- Review reuse of [`mergeSilentPreviewFromServer`](frontend/recipe_graph_editor/src/mergeSilentPreviewFromServer.ts).

Later may raise concurrency to 2–3 after stabilization.

### 7) Other call sites

- `macro_pattern_staff_api_recipe_graph_recompute`, etc.: keep `sync_png=True` per policy (fill once after save) or same defer + client warm — **initially recommend keeping existing sync** (minimal change scope).

---

## Implementation order (todo names)

1. **renderer-cache-only**: cache-only lookup API (`render_cached_only`, etc.)
2. **macro-html-no-sync-render**: `serialize_graph_node(..., sync_png=False)` + macro graph HTML only
3. **staff-preview-warm-endpoint**: POST warm view + `urls.py` + cache_key↔scene validation
4. **client-preview-warm-queue**: sequential fetch + CSRF + node data update
5. **cache-key-scene-payload-store** (optional · phase 2): TTL cache to shrink HTML payload + warm with cache_key only

---

## Tests

- Unit: on miss with `sync_png=False` no generation call; on hit URL present
- Integration: one warm POST → `GraphPreviewImage` (or file) exists and response URL

---

## References

- Image URL keeps existing namespace: [`web:graph_preview_cache`](django_apps/web/urls.py).
- Tile already blocks WebGL fallback; before warm only shortcode/scene fallback may show.
