# Cross-Reference Analysis — `materials.json`

## Relationship diagram

```text
game_data_import_batch
  └─ has many → material_asset (4 rows)

material_asset
  └─ referenced by → asset_meta_reference (asset_kind = material)
        └─ meta_stable_id on .meta side (asset_references.json)

material_asset (logical names)
  └─ inferred use → buildings / HUD / fluid mixer rendering
        (no direct stable_id in buildings.json — path-level only)
```

## FK relationships

| From | To | Cardinality | Resolution |
| ---- | -- | ----------- | ---------- |
| `material_asset` | `game_data_import_batch` | N:1 | `import_batch_id` |
| `asset_meta_reference` | `material_asset` | N:1 | `ref_stable_id` = `stable_id` (4/4) |

## M2M

None.

## Ordered children

None in `materials.json` (flat list). Optional ordering by `source_row_index` for deterministic imports.

## Inferred references by ID

| Reference | Target | Status |
| --------- | ------ | ------ |
| Each `stable_id` | one `asset_references` material row | **resolved** (4/4) |
| `MixerFluidMaterial` | fluid mixer UI | **inferred** — no JSON FK |
| `PainterRoll*` | painter buildings | **inferred** — review building variants |

## Unresolved references

| Item | Issue |
| ---- | ----- |
| Shader / texture slots | Not in dump |
| `display_name_key` → translated string | `translations.json` empty |
| Building → material FK | No explicit ID in `buildings.json` |

## Source metadata references

- `source_type_name: UnityEngine.Object` on every row
- Empty `source_guid`

## Unknown / review

- Whether planner needs material rows or only `asset_meta_reference` bridge
