# Cross-Reference Analysis — `sprites.json`

```text
game_data_import_batch
  └─ has many → sprite_asset (61)

sprite_asset
  └─ referenced by → asset_meta_reference (asset_kind = sprite, 61 links)

sprite_asset (icon path)
  └─ inferred UI for → building_variant / toolbar / HUD
        (name overlap only — no stable_id in building JSON)
```

## FK

| From | To | Resolution |
| ---- | -- | ---------- |
| `sprite_asset` | `game_data_import_batch` | N:1 |
| `asset_meta_reference` | `sprite_asset` | `ref_stable_id` = `stable_id` (61/61) |

## Unresolved

- Atlas/texture GUIDs not in dump
- Building variant → sprite FK

## Source metadata

- `UnityEngine.Object`, empty `source_guid`
