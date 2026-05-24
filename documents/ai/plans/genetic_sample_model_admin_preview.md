# Genetic sample (GeneticSample) — implementation notes

**Status**: ACTIVE (implementation in progress)  
**Purpose**: On save, decode Shapez2 copy string (`SHAPEZ2-4-…`) into `decoded_json`; Django Admin shows **island-local** coordinate mini grid + preview with `web/assets/sprites/` sprites.

## Decisions

- App: `asteroid_lab`. Model `GeneticSample`.
- Decode: `decode_copy_string` → `normalize_decoded_blueprint` → island coord meta (same pipeline as map input; PR-F: no server attach).
- Validation failure: block save via `ValidationError` in `Model.clean()`.
- Sprite filename rules: **mirror in Python module** from `LAB_SPRITE_KNOWN` / `labSpriteFilenameForCell` in `asteroid_miner_layout_lab.js` (comment cites JS location).
- Admin grid: column/row count from `full_map_island_bbox` / island `(x,y)` (left-bottom anchor).
- Optional fields: `name`, `project` (nullable FK `AsteroidProject`).

## Reference code

- `django_apps/asteroid_lab/adapters/decode_adapter.py`
- `django_apps/asteroid_lab/snapshots/decoded_blueprint_snapshot.py`
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
