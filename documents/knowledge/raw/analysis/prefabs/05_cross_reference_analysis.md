# Cross-Reference Analysis — `prefabs.json`

## Relationship diagram

```text
game_data_import_batch
  └─ has many → prefab_asset (764)

prefab_asset
  └─ referenced by → asset_meta_reference (asset_kind = prefab, 764 links)

prefab_asset (path_family / LOD flags)
  └─ inferred presentation for → building / transport / wire systems
        (building_variants.json — no stable_id FK in JSON)

building_variant
  └─ (no direct FK in dump) — name/path correlation only
```

## FK relationships

| From | To | Cardinality | Resolution |
| ---- | -- | ----------- | ---------- |
| `prefab_asset` | `game_data_import_batch` | N:1 | `import_batch_id` |
| `asset_meta_reference` | `prefab_asset` | 764:1 | `ref_stable_id` |

## M2M

None in this file.

## Ordered children

None; deterministic order via `source_row_index` (= array index).

## Inferred references

| Reference | Status |
| --------- | ------ |
| Meta `ref_stable_id` → `stable_id` | **resolved** 764/764 |
| `Pipe_*` prefabs ↔ `belts_pipes_transport.json` | **inferred** by path name |
| `Wire_*` ↔ wire variants | **inferred** |
| `building_variants` (131) ↔ prefabs (764) | **unresolved** — many LOD meshes per building |

## Unresolved

- Component/mesh GUIDs inside Unity prefab
- Explicit building_variant_id FK
- Translated display strings (`translations.json` empty)

## Source metadata

- `UnityEngine.Object`, empty `source_guid` on all rows
