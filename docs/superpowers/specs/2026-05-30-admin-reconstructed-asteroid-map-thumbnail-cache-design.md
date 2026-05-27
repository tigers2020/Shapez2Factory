# Admin Reconstructed Asteroid Map — Changelist Thumbnail Cache — Design Spec

**Date:** 2026-05-30  
**Status:** Approved (Approach B + amendments below)  
**Scope:** `ReconstructedAsteroidMap` Django Admin changelist performance only  
**Out of scope (v1):** `GeneticSample` admin, detail `mini_map_preview` HTML replacement, solver/replay inputs

---

## Problem

`ReconstructedAsteroidMapAdmin` changelist calls `genetic_sample_mini_map_html(decoded_json, for_list=True)` per row. Cost is roughly **page_rows × O(W×H)** HTML/DOM generation plus loading large `decoded_json` JSONFields. Large `full_map_island_bbox` (exterior envelope) makes W×H far larger than occupied cell count E, so load time grows superlinearly with map extent.

## Goal

Changelist shows one cached **WebP lossless** (PNG fallback) `<img>` per row. Detail change form keeps existing `mini_map_preview` HTML renderer.

## Non-goals (v1)

- JPG thumbnails (forbidden: grid/sprite readability)
- Using thumbnails as solver, replay, or algorithm inputs
- Replacing `decoded_json` as source of truth
- Detail-page image cache (phase 2)

---

## Approach B (approved)

```text
persist / explicit regen → raster thumbnail → ImageField
changelist → <img src=...> only (no genetic_sample_mini_map_html)
change form → existing mini_map_preview unchanged
```

---

## Invariants (output-only artifact)

| Rule | Requirement |
|------|-------------|
| Source of truth | `decoded_json` on `ReconstructedAsteroidMap` |
| Thumbnail role | Admin display artifact only |
| Cache key | `canonical_hash(decoded_json)` + `admin_list_thumbnail_renderer_version` |
| Algorithm | Must not read thumbnail files or URLs |

**Forbidden formats:** JPEG/JPG.

**Allowed formats:** WebP lossless (primary), PNG (fallback when WebP save fails).

---

## Data model

Add to `ReconstructedAsteroidMap`:

| Field | Type | Notes |
|-------|------|-------|
| `admin_list_thumbnail` | `ImageField` | `upload_to="reconstructed_maps/list/%Y/%m/"`, `blank=True` |
| `admin_list_thumbnail_hash` | `CharField(max_length=64, blank=True)` | SHA-256 hex of canonical JSON |
| `admin_list_thumbnail_renderer_version` | `CharField(max_length=16, blank=True)` | e.g. `"1"` |
| `admin_list_thumbnail_cell_count` | `PositiveIntegerField(default=0)` | BP entry count used for render |
| `admin_list_thumbnail_grid_w` | `PositiveSmallIntegerField(default=0)` | Grid width drawn |
| `admin_list_thumbnail_grid_h` | `PositiveSmallIntegerField(default=0)` | Grid height drawn |
| `admin_list_thumbnail_truncated` | `BooleanField(default=False)` | Bbox cap applied |

Storage: default `MEDIA_ROOT` / `MEDIA_URL` (`config/settings.py`).

---

## Invalidation

Regeneration decision is based on **`canonical_hash(decoded_json)` compared with stored `admin_list_thumbnail_hash`**, and **`admin_list_thumbnail_renderer_version` compared with current renderer constant** — not implicit Django model dirty tracking.

```text
if hash != stored_hash OR renderer_version != current OR force:
    regenerate
else:
    skip
```

Empty or invalid `decoded_json` (no drawable BP): clear thumbnail fields; changelist shows placeholder.

---

## Save hook / recursion guard

Thumbnail regeneration **must not** recursively trigger full model `save()` without a guard.

**Allowed patterns (v1 uses #1 + #3):**

1. **Service-level:** `persist_reconstructed_asteroid_map` calls thumbnail sync after `update_or_create` / `save` of JSON fields.
2. **post_save with guard:** only if paired with `QuerySet.update(...)` on thumbnail fields and a re-entrancy flag (not preferred alone).
3. **Explicit:** admin actions and `manage.py regenerate_reconstructed_map_thumbnails`.

**Required implementation rule:** after `FileField.save(..., save=False)`, capture `thumbnail_name = row.admin_list_thumbnail.name` and persist via `QuerySet.update(admin_list_thumbnail=thumbnail_name, ...)` so the DB column stores the storage path. Do **not** update only hash/metadata columns while omitting `admin_list_thumbnail`. Avoid full `row.save()` without a recursion guard.

**Thumbnail failure containment:** `sync_admin_list_thumbnail` must **never** raise through to `persist_reconstructed_asteroid_map` or other primary writes. On render/storage failure: log warning, `clear_admin_list_thumbnail(pk)`, return (changelist shows placeholder). Narrow catches: `ValueError`, `OSError`, and Pillow errors — not bare suppression of DB/integrity errors.

---

## Render pipeline (bounded Big-O)

**Input:** `decoded_json` dict.

1. `build_decoded_blueprint_snapshot(decoded_json)` — **O(E)**.
2. Bbox: **`snap.bbox_json` (tight, cells only)** — do **not** use `full_map_island_bbox` for list thumbnails (excludes exterior void envelope).
3. **Cap:** `ADMIN_LIST_THUMBNAIL_MAX_GRID = 48` per axis. If `width` or `height` exceeds cap, crop window centered on occupied cells; **clamp** `min_x`/`min_y` and derived `grid_w`/`grid_h` so the window stays inside the tight bbox (`max_x`/`max_y` bounds); set `admin_list_thumbnail_truncated=True`.
4. Iterate **occupied cells only** within the window — **O(min(E, cap²))**, never dense empty grid fill.
5. **Renderer v1 (primary):** Pillow color-block raster by `cell_kind` / `tile_type` prefix (aligned with admin dark theme).
6. **Optional enhancement:** SVG sprite compositing via `cairosvg` when importable; on failure, fall back to color-block (must not fail save).
7. Output: max edge **256px**; save WebP lossless; PNG if WebP fails.
8. Constants module: `ADMIN_LIST_THUMBNAIL_RENDERER_VERSION = "1"`.

---

## Admin integration

### Changelist

- Replace `mini_map_list` implementation with `admin_list_thumbnail` `<img>` (lazy, fixed max dimensions).
- Placeholder when missing: muted box + cell count / `truncated` hint; link to change form optional.
- **`get_queryset`:** defer `decoded_json` and `original_decoded_json` **only** when `request.resolver_match.url_name` ends with `_changelist`.

### Change form

- Keep `mini_map_preview` → `genetic_sample_mini_map_html(obj.decoded_json)` unchanged.
- Do **not** defer JSON on change/history views.

### Actions

- `regenerate_admin_list_thumbnails` — loads `decoded_json` via explicit queryset (no defer).
- `clear_admin_list_thumbnails` — clears file + hash fields.

### Management command

`python manage.py regenerate_reconstructed_map_thumbnails [--pk ID] [--all] [--force]`

Must use queryset that **includes** `decoded_json` (no changelist defer).

---

## Queryset defer scope (amendment)

```text
Admin changelist queryset defers large JSON fields.
Regeneration command/action must explicitly load decoded_json in a controlled queryset.
```

---

## Performance targets

| Item | Target |
|------|--------|
| Changelist | No per-row `genetic_sample_mini_map_html` |
| Changelist DOM | ~1 `<img>` per row |
| Changelist JSON | No `decoded_json` load on changelist (defer) |
| Save | One bounded thumbnail render when hash/version changes |
| Failure | Changelist still loads; placeholder shown |

---

## Testing

| Area | Cases |
|------|-------|
| Hash | Stable canonical JSON; version bump triggers regen |
| Render | Truncated when bbox > cap; O(cells) smoke |
| Persist hook | Save updates thumbnail; hash match skips regen |
| Persist + render failure | `persist_reconstructed_asteroid_map` succeeds; thumbnail cleared |
| Admin changelist HTML | No `genetic-sample-mini-map-cell` in changelist response |
| Command / action | Regenerate and clear paths; `call_command --pk --force` |
| Recursion | Double persist does not infinite-loop |
| DB path | After sync, `admin_list_thumbnail.name` non-empty on row |

---

## Rollout

1. Migration + deploy code.
2. `regenerate_reconstructed_map_thumbnails --all` (or batched) for existing rows.
3. Verify changelist latency and placeholder rate.

## Phase 2 (deferred)

- Detail `mini_map_preview` image cache.
- Collapsed / lazy `decoded_json_pretty`.
- Sprite-quality thumbnail when `cairosvg` is a committed dependency.

---

## Approval record

```text
APPROVE: Approach B — changelist-only WebP/PNG thumbnail cache
Amendments: save recursion guard, hash-based invalidation wording, color-block primary renderer,
            changelist-only defer, action/command test paths,
            ImageField name in QuerySet.update, thumbnail failure must not fail persist,
            crop window upper-bound clamp
PLAN: APPROVED AFTER BLOCKER FIXES (2026-05-30 review)
```
