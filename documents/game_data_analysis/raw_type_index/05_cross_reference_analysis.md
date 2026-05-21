# Cross-Reference Analysis — `raw_type_index.json`

## Relationship diagram

```text
game_data_import_batch
  └─ has many → clr_type_registry_entry (6497)

clr_type_registry_entry
  ├─ (type_name) ← optional lookup from → items.json / buildings.json (source_type_name)
  └─ (assembly_name) → inferred link → manifest.assembly_hashes (Game.Content.dll)

manifest.assembly_hashes
  └─ documents → CLR assemblies at dump time (198 DLLs)

prefab_asset / material_asset
  └─ (no FK) — content dumps use UnityEngine.Object, not indexed here
```

## FK relationships

| From | To | Cardinality | Resolution |
| ---- | -- | ----------- | ---------- |
| `clr_type_registry_entry` | `game_data_import_batch` | N:1 | `import_batch_id` |
| Other dumps → registry | optional lookup | N:0..1 | `source_type_name` = `type_name` (assembly ambiguous if multiple) |

## M2M

None.

## Ordered children

None; preserve `source_row_index` for deterministic re-import.

## Inferred references

| Reference | Status |
| --------- | ------ |
| `ShapeItem` in index | **resolved** (`items.json`) |
| `assembly_name` ↔ `Game.Content.dll` | **inferred** name match to manifest |
| `SpaceConveyorSimulationRenderer` ↔ simulation | **inferred** by name only |
| `asset_references.ref_stable_id` | **no link** |

## Unresolved

- `source_type_name` in dumps without `assembly_name` in same row → join may be **1:N** on `type_name` alone
- Full assembly-qualified type names (with `Version=…`) not present in `type_name` field
- Which of 6497 types are planner-relevant vs noise

## Source metadata

- Empty paths/GUIDs on all rows
- Duplicate `stable_id` across assemblies (Unity generated types)

## Unknown / review

- Filter policy for 1,892 compiler-generated rows in planner DB
