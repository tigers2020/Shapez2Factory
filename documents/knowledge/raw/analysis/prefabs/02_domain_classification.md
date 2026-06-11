# Domain Classification — `prefabs.json`

## Per-element fields

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `[i]` | domain entity | → `prefab_asset` |
| `[i].stable_id` | entity attribute | Unique content hash |
| `[i].prefab_path` | entity attribute | Canonical resource path |
| `[i].source_path` | entity attribute | Redundant with `prefab_path` in dump |
| `[i].display_name_key` | entity attribute | i18n key (no translations yet) |
| `[i].source_type_name` | source metadata | `UnityEngine.Object` |
| `[i].source_guid` | source metadata | Empty |
| Path prefix (`Wire`, `Pipe`, …) | unknown / needs human review | Inferred family tag only |

## Rejected as domain entities

| Label | Reason |
| ----- | ------ |
| `UnityEngine.Object` | Exporter channel |
| `ConstantSignal_Main_BakedMesh_Main_LOD0` as table name | Single prefab path, not entity type |
| 764 tables | Anti-pattern |

## Inferred domain entities

| Entity | Evidence |
| ------ | -------- |
| **Prefab asset** | 764 unique content rows |
| **Import batch** | `manifest.json` |

## Relationships (external)

| From | To | Via |
| ---- | -- | --- |
| `asset_meta_reference` | `prefab_asset` | `ref_stable_id` = `stable_id` |
| Building simulation (inferred) | `prefab_asset` | Path substring / art pipeline — **no JSON FK** |
