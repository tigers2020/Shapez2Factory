# JSON Path Mapping — `materials.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[i]` | Material row | domain entity | `material_asset` | — | — | `source_row_index = i` |
| `[i].stable_id` | Content hash | entity attribute | `material_asset` | `stable_id` | — | UNIQUE |
| `[i].material_path` | Material resource name | entity attribute | `material_asset` | `material_path` | — | UNIQUE |
| `[i].source_path` | Asset path string | entity attribute | `material_asset` | `logical_path` | — | equals material_path |
| `[i].display_name_key` | Localization key | entity attribute | `material_asset` | `display_name_key` | — | |
| `[i].source_type_name` | Dump type channel | source metadata | `material_asset` | `dump_source_type` | — | not domain name |
| `[i].source_guid` | Unity GUID | source metadata | `material_asset` | `unity_source_guid` | — | empty |
| `manifest.file_hashes.materials.json` | File digest | source metadata | `game_data_import_batch` | via artifact row | integrity | |
| `asset_references[*].ref_stable_id` | Meta → content | relationship | `asset_meta_reference` | `content_stable_id` | FK | 4 resolves |
| (unmapped keys) | — | unknown | `unknown_property` | — | audit | |

## Row inventory (all 4)

| Index | `material_path` | `stable_id` (prefix) |
| ----- | --------------- | -------------------- |
| 0 | LabelTextMaterial | a77f995f… |
| 1 | MixerFluidMaterial | 7074a3f1… |
| 2 | PainterRollMaterial | b590aded… |
| 3 | PainterRollMinimalMaterial | 23b54991… |
