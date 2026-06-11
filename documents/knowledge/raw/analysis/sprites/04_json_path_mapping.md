# JSON Path Mapping — `sprites.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ----- |
| `[i].stable_id` | Content hash | entity attribute | `sprite_asset` | `stable_id` | UNIQUE |
| `[i].sprite_path` | Sprite name | entity attribute | `sprite_asset` | `sprite_path` | UNIQUE |
| `[i].source_path` | Asset path | entity attribute | `sprite_asset` | `logical_path` | |
| `[i].display_name_key` | i18n key | entity attribute | `sprite_asset` | `display_name_key` | |
| `[i].source_type_name` | Dump channel | source metadata | `sprite_asset` | `dump_source_type` | |
| `[i].source_guid` | Unity GUID | source metadata | `sprite_asset` | `unity_source_guid` | empty |
| `(inferred)` | Icon family | unknown | `sprite_asset` | `icon_family` | optional |
| `asset_references[*].ref_stable_id` | Meta link | relationship | `asset_meta_reference` | `content_stable_id` | 61 FKs |
| `manifest.file_hashes.sprites.json` | File digest | source metadata | artifact checksum | — | |
