# JSON Path Mapping — `prefabs.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[i]` | Prefab row | domain entity | `prefab_asset` | — | — | `source_row_index=i` |
| `[i].stable_id` | Content hash | entity attribute | `prefab_asset` | `stable_id` | — | UNIQUE |
| `[i].prefab_path` | Prefab name/path | entity attribute | `prefab_asset` | `prefab_path` | — | UNIQUE |
| `[i].source_path` | Asset path | entity attribute | `prefab_asset` | `logical_path` | — | = prefab_path |
| `[i].display_name_key` | i18n key | entity attribute | `prefab_asset` | `display_name_key` | — | |
| `[i].source_type_name` | Dump channel | source metadata | `prefab_asset` | `dump_source_type` | — | |
| `[i].source_guid` | Unity GUID | source metadata | `prefab_asset` | `unity_source_guid` | — | empty |
| `(inferred)` | Wire/Pipe/… family | unknown | `prefab_asset` | `path_family` | inferred | parse rules |
| `(inferred)` | LOD in name | unknown | `prefab_asset` | `is_lod_variant` | inferred | |
| `manifest.file_hashes.prefabs.json` | File digest | source metadata | artifact checksum | `expected_sha256` | — | |
| `asset_references[*].ref_stable_id` | Meta link | relationship | `asset_meta_reference` | `content_stable_id` | FK | 764 rows |
