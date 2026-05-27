# Lab map: rendering · direction contract (implementation notes)

Not CANON. Keep in sync with [`django_apps/web/static/web/js/asteroid_miner_layout_lab.js`](../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js).

## Canonical direction

- Integer `0–3`: **0 = East, 1 = South, 2 = West, 3 = North**
- Quarter-turn is **clockwise** (same sign sense as `rotate(90deg)` on screen).
- Server/domain `cell.rotation` values are **unchanged for display and storage.** Lab sprites apply domain R only via CSS `rotate` on East-facing assets.

## Domain rotation contract (summary)

- **R = 0 → East**, R increases by **clockwise** quarter-turn.
- **No per-file rotation offset registry.** Apply only `normalizeQuarterTurns(cell.rotation)` → `rotate(90deg × R)` on `<img>`.
- Do not add arbitrary transforms like `+1` to domain `R`.

## Verification procedure (rotation issues)

- R overlay via `data-lab-debug-rotation="1"` on `#lab-root`.
- For a few cells, record `tile_type` / sprite file / server `R` / expected direction and confirm **domain R matches screen direction**.

## Sprites

### Sprite key policy

| Field | Responsibility | Example |
|------|----------------|---------|
| `cell_kind` / `kind` | Domain meaning (`space_belt`, `space_pipe`, etc.) | **Do not unify with Identifier** |
| `tile_type` | **Canonical sprite key** = blueprint `T` = `ShapezGameIdentifier.value` | `SpaceBelt_Forward`, `SpacePipe_LeftTurn` |
| `sprite_identifier` | **alias** of `tile_type` (both emitted in wire JSON) | always same as `tile_type` |
| `transport_kind` / `transport` | Domain channel (`shape_belt`, `fluid_pipe`) | **not used directly** for sprite lookup |
| `rotation` | quarter-turn (0–3) | CSS `rotate(90deg × R)` with no extra transform |

**Transport (belt/pipe) sprites require `tile_type` (= `sprite_identifier`).** `cell_kind = space_belt` alone cannot distinguish variants (`Forward` / `LeftTurn` / `TripleSplitter`, etc.), so no sprite is chosen. Materializer `pick_tile_type` produces canonical T values.

### JS sprite resolution order

1. `cell.sprite_identifier || cell.tile_type` → `labIdentifierSpriteRelpaths[t]` (DB path).
2. Else prefix fallback: `SpaceBelt_*` → `SpaceBelt/<T>.svg`, `SpacePipe_*` → `SpacePipe/<T>.svg`, `Layout_*` → `Miner/<T>.svg` (`LAB_SPRITE_TILE_TYPE_ALIASES` maps `Layout_ProMiner` → `Layout_ShapeMiner`, etc.).
3. Else `cell_kind` → `LAB_SPRITE_CELL_KIND_TO_IDENTIFIER` (miner/extension only).
4. Last fallback: `inferTransportSpriteIdentifier(cell)` — returns `Forward` variant only (turn/splitter skipped without `tile_type`).

### Wire JSON contract

`timeline_serialization.replay_map_view_to_json_dict` always emits both fields on each cell in `full_cells` / `overlay_cells` / `cell_delta`:

```json
{ "tile_type": "SpaceBelt_Forward", "sprite_identifier": "SpaceBelt_Forward" }
```

`sprite_identifier` is identical to `tile_type` with no extra processing. Consumers (JS / third party) may read either.

### LAB_SPRITE_KNOWN (legacy name, absent now)

Prior docs mentioned `LAB_SPRITE_KNOWN` whitelist and `labSpriteFilenameForCell`; current JS has neither. Resolution order above and `labIdentifierSpriteRelpaths` (DB path map) are canon.

- Django Admin genetic sample minimap uses `lab_sprite_resolve(tile_type, cell_kind, rotation)` in `django_apps/asteroid_lab/admin_lab_sprites.py` to bind **T·kind→file** and **R→display quarter** (no R offset in file selection).

## Admin minimap vs Lab replay (grid)

- **Admin genetic minimap**: draws only **tight** server bbox grid from `decoded_json`. Cell wrappers have contract attrs `data-server-x` / `data-server-y` / `data-grid-row` / `data-grid-col` / `data-linear-index` / `data-sprite` / `data-rotation-deg` (`django_apps/asteroid_lab/genetic_sample_mini_map.py`; coords same as `mini_map_grid_coord` in `django_apps/asteroid_lab/lab_screen_grid.py`).
- **Admin reconstructed map changelist**: cached WebP/PNG `admin_list_thumbnail` on `ReconstructedAsteroidMap` (tight cell bbox, cap 48, color-block raster). Display-only — not solver/replay input. Detail change form still uses `genetic_sample_mini_map_html` for `mini_map_preview`.
- **Lab replay**: same dense/raw **relative neighbor** rules (`visualCol` + raw `y`) but may have **symmetric padding**; do **not** compare absolute cell indices directly with Admin.
- **Replay grid bbox** (`computeReplayGridLayout`): when scanning all frames, include **`map_view.overlay_cells`** and **`map_view.cell_delta`** coords in spatial targets, not only `map_view.full_cells`.
- **RTTP compose dual-channel clip** (`lab_rttp_snapshot_compose.clip_overlay_cells_to_base_map_domain`): equipment rows stay on mineable **anchors**; transport/route rows use a **dynamic render envelope** (`build_lab_render_bbox`: projected `full_cells` ∪ projected raw overlay, pre-clip) plus `known_route_render_domain`. Exterior void connector belts may expand the envelope beyond asteroid `full_cells`. Spec: `docs/superpowers/specs/2026-05-30-rttp-replay-route-overlay-clip-design.md`.
- **Reconstruction trace** (Wall Projection, Flood Seed, etc.): Lab unified adapter promotes `_replay_trace` markers in `frame_payload.diff.added` to **`map_view.overlay_cells`** and keeps wire JSON top-level **`diff`** (JS `renderDiffOverlays` assist). When miner/belt exist only on overlay in optimization `validation.completed`, etc., bbox must not drop them so `resolveCellIndex` silently skips (`collectFrameSpatialTargets` ↔ same coord set as overlay paint in `renderReplayFrame`).
- **Rotation quarter** is independent of coord correction. Statements about which screen direction is right/down are **only asserted where tests · `data-*` prove them** (do not fix by declaration alone).
- Screen quarter-turn uses `normalizeQuarterTurns(serverRotation)` only.
- Sprites render **only via `<img class="lab-cell-sprite">`**, not `background-image`. Rotation **`transform` on `img` only.** For vector SVG zoom use **`image-rendering: auto`** (`crisp-edges` on `<img>` vectors can blur/pixelate).
- Base URL from `#lab-root` `data-lab-sprite-base` (Django `{% static 'web/assets/sprites/' %}`).

## Cell shape · size

- Lab replay grid cells (`.lab-cell`, `.lab-cell-sprite-layer`) are **rounded rectangles**. Use `#lab-replay-grid` `--lab-cell-radius` (default 4px; JS updates in `applyLabGridLayoutForZoom`).
- Formula: `round(cellPx × 0.14)`, clamp **`[2, 7]`** px. Demo SSR default cell is `h-7 w-7` (28px); replay fit cap `maxCell` 36px.
- Admin genetic minimap (`genetic_sample_mini_map`) applies same ratio as inline `border-radius` (`_mini_map_cell_radius_px`; default `cell_px` 52).

## Bundle bridge

- Unified timeline JSON (`lab_replay_frames_json`) includes **`cell_overlay_json.equipment_bundles`** when present. Lab JS `cellOverlayJsonFromFrame` → `applyEquipmentBundleGroupVisualsFromOverlay` draws outline (`bundle_edges`) and links (`bundle_links`). Optimization frames recompute bundles on server from `map_view` cells.
- `bundle_links` string `e` / `s` / `w` / `n` go through `LINK_KEY_TO_DIR` → `DIR_TO_BRIDGE_SUFFIX` to `lab-bundle-bridge-*` classes only (geometry aligned with [`assets/css/input.css`](../../assets/css/input.css) `#lab-replay-grid --lab-cell-gap`).

## Viewport

- `#lab-replay-grid-viewport` stays **16:9** fixed ratio (`aspect-video`, etc.) as **layout size · clipping window** only. `overflow: hidden`, `contain: layout paint`, `touch-action: none`, etc. reduce browser gesture/selection overlap. **Do not put `transform` or zoom-driven inline `width`/`height` on viewport.**
- `#lab-replay-grid-stage` is `position: absolute; left: 0; top: 0; transform-origin: 0 0` and is the **sole CSS transform owner** for pan/zoom. JS applies `transform: translate(tx, ty) scale(zoom)` once. Snap `tx`/`ty` to **device pixels** (`snapToDevicePixel`). Pass `zoom` unchanged to `scale`. Avoid unnecessary `will-change: transform` on stage (compositing layer rasterized at unscaled size then scaled can blur sprites).
- `#lab-replay-grid` `grid-template-columns` / `rows` use **world cell edge (px) independent of zoom** (server replay: `replayFitBasePx`, demo: `demoBaseCellPxAtZoom1`). Do not multiply cell size by `zoom`.
- `#lab-optimization-overlay-layer` sits **inside** stage as sibling of `#lab-replay-grid`, sharing stage transform (overlay does not own viewport transform).
- Pointer hit test · HUD: after viewport padding correction, inverse `(viewportLocal - translate) / zoom` to **world coords** for cell index.

## Debug

- When `#lab-root` has `data-lab-debug-rotation="1"` or JS constant `LAB_DEBUG_ROTATION` is true, `#lab-replay-grid` gets `lab-debug-rotation` class and R overlay shows when `data-r` is set on cells with sprites.

## SVG assets

- New Lab layout sprites should be authored **East-facing**.
- Prefer `viewBox="0 0 100 100"`; existing 96 coordinate system can be wrapped with scale.
