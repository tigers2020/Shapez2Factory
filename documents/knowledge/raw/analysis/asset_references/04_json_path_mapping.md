# JSON Path Mapping — `asset_references.json`

Notation: `[*]` = each array element (829 rows). `→` = maps on import.

## Primary mappings (this file)

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[*]` | One meta reference record | domain entity | `asset_meta_reference` | (row) | — | Root array element |
| `[*].stable_id` | Meta registry hash ID | domain entity (id) | `asset_meta_reference` | `meta_stable_id` | PK natural | Not referenced elsewhere in bundle |
| `[*].ref_stable_id` | Content asset hash ID | relationship | `asset_meta_reference` | `content_stable_id` | FK → content table | 100% resolves in sibling files |
| `[*].asset_type` | Content kind discriminator | enum / choice | `asset_meta_reference` | `asset_kind` | FK selector | `prefab` \| `sprite` \| `material` |
| `[*].source_path` | Unity logical asset path | entity attribute | `asset_meta_reference` | `logical_path` | unique natural key | Matches linked content `source_path` |
| `[*].display_name_key` | Display/i18n key | entity attribute | `asset_meta_reference` | `display_name_key` | — | Currently identical to `source_path` |
| `[*].source_guid` | Exporter label (not GUID) | source metadata | `asset_meta_reference` | `source_label` | — | **Human review:** misnamed in JSON |
| `[*].source_type_name` | Dump capture type | source metadata | `asset_meta_reference` | `dump_source_type` | — | Constant `asset.meta` |
| `[].$index` | Array position | source metadata | `asset_meta_reference` | `source_row_index` | ordered child | Preserve for deterministic audit |

## Polymorphic FK resolution (`ref_stable_id` + `asset_type`)

| JSON path | Target table (when `asset_type` =) | Target column |
| --------- | ------------------------------------ | ------------- |
| `[*].ref_stable_id` | `prefab_asset` | `stable_id` |
| `[*].ref_stable_id` | `sprite_asset` | `stable_id` |
| `[*].ref_stable_id` | `material_asset` | `stable_id` |

| `asset_type` value | Target table |
| ------------------ | ------------ |
| `prefab` | `prefab_asset` |
| `sprite` | `sprite_asset` |
| `material` | `material_asset` |

## Sibling file mappings (FK targets — not in `asset_references.json`)

| JSON path (sibling) | Target table | Target column | Linked from |
| ------------------- | ------------ | ------------- | ----------- |
| `prefabs.json[*].stable_id` | `prefab_asset` | `stable_id` | `asset_meta_reference.content_stable_id` |
| `prefabs.json[*].source_path` | `prefab_asset` | `logical_path` | denormalized match |
| `prefabs.json[*].prefab_path` | `prefab_asset` | `prefab_path` | content resource |
| `prefabs.json[*].display_name_key` | `prefab_asset` | `display_name_key` | |
| `prefabs.json[*].source_type_name` | `prefab_asset` | `dump_source_type` | source metadata |
| `sprites.json[*].stable_id` | `sprite_asset` | `stable_id` | FK |
| `sprites.json[*].sprite_path` | `sprite_asset` | `sprite_path` | |
| `materials.json[*].stable_id` | `material_asset` | `stable_id` | FK |
| `materials.json[*].material_path` | `material_asset` | `material_path` | |

## Manifest / provenance mappings

| JSON path | Target table | Target column | Notes |
| --------- | ------------ | ------------- | ----- |
| `manifest.json → file_hashes → asset_references.json` | `game_data_import_batch` | `file_hash` | Integrity gate |
| `manifest.json → dump_schema_version` | `game_data_import_batch` | `dump_schema_version` | Version drift detection |

## Fields intentionally not mapped to domain tables

| JSON path | Reason |
| --------- | ------ |
| *(none today)* | Schema is closed; future keys → `unknown_property` |

## Unmapped / derived-only

| Derived concept | Source paths | Target |
| --------------- | ------------ | ------ |
| `content_checksum` | all scalar fields + index | `asset_meta_reference.content_checksum` |
| Path suffix facets (`_LOD2`, `BakedMesh`) | `[*].source_path` parse | **optional** `asset_path_variant_hint` — **inferred, not implemented yet** |
