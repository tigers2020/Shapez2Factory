# Import Pipeline — `sprites.json`

**Prerequisites:** `manifest.json` verified.

**Order:** Import **`sprites.json` before `asset_references.json`**.

1. Load UTF-8-SIG; verify hash `802f9fb6…`.
2. Validate 61 rows; unique `stable_id` and `sprite_path`.
3. Normalize empty guid → NULL; optional `icon_family` parse.
4. Source metadata per index (optional).
5. Sample indices 4, 25, 28 (seed 20260521).
6. DTO `SpriteAssetDTO`.
7. Validate required keys; path triple equality.
8. Upsert `sprite_asset` on `stable_id`.
9. No child entities.
10. After asset_references import: 61 sprite meta refs resolve.
11. Invariants: count 61; no orphans.
12. Audit: path list, manifest hash.

## Idempotency

Keys: `stable_id`, `sprite_path`.
