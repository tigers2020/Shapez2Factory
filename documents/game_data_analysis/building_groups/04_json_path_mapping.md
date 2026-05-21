# JSON Path Mapping — `building_groups.json`

## Envelope mappings

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[*]` | One building group | domain entity | `building_group` | (row) | — | 67 rows |
| `[*].stable_id` | Groups-file hash ID | domain entity (id) | `building_group` | `registry_stable_id` | unique | ≠ buildings `stable_id` |
| `[*].source_guid` | Group business key | domain entity key | `building_group` | `group_key` | unique | |
| `[*].display_name_key` | Lazy title ref | entity attribute | `building_group_localization_ref` | `title_key` | | Parse LazyText |
| `[*].description_key` | Lazy description ref | entity attribute | `building_group_localization_ref` | `description_key` | | |
| `[*].simulation_parameters` | Sim/UI flags | entity attribute | `building_group_simulation_setting` | (row) | 1:1 | Strip backing fields |
| `[*].simulation_parameters.IsTransportBuilding` | Transport flag | entity attribute | `building_group_simulation_setting` | `is_transport_building` | | |
| `[*].simulation_parameters.PipetteOverrideId.Id` | Pipette id | entity attribute | `building_group_simulation_setting` | `pipette_override_id` | | Often `""` |
| `[*].simulation_parameters.ShowStat*` | Stat toggles | entity attribute | respective columns | | |
| `[*].source_type_name` | Dump capture type | source metadata | import audit | `dump_capture_type` | | |
| `[*].source_path` | Unity path | source metadata | — | — | | Empty |
| `[*].definition_snapshot` | Full group graph | relationship payload | `building` (dedupe) | `snapshot_content_hash` | dedupe | Same as buildings file |

## Group snapshot attribute mappings

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.Id.Id` | `building_group` | `group_key` (confirm) |
| `[*].definition_snapshot.IsTransportBuilding` | `building_group` | `is_transport_building` |
| `[*].definition_snapshot.DefaultPreferredPlacementMode` | `building_group` | `placement_mode` |
| `[*].definition_snapshot.PlayerBuildable` | `building_group` | `player_buildable` |
| `[*].definition_snapshot.Selectable` | `building_group` | `selectable` |
| `[*].definition_snapshot.Removable` | `building_group` | `removable` |
| `[*].definition_snapshot.AutoConnect` | `building_group` | `auto_connect` |
| `[*].definition_snapshot.Icon` | — | audit only (`$unity`) |
| `[*].definition_snapshot.Title` / `Description` | — | prefer LazyText envelope keys |

## Definitions[] membership mappings

| JSON path | Target table | Target column | Notes |
| --------- | ------------ | ------------- | ----- |
| `[*].definition_snapshot.Definitions[]` | `building_group_member` | (row) | ordered child |
| `[*]....Definitions[i].Id.Name` | `building_group_member` | `internal_variant_name` | FK lookup |
| `[*]....Definitions[i]` (full embed) | `building_variant` | via import dedupe | Prefer variant file |
| `[*]....Definitions[i].$cycle` | `building_group_member` | `cycle_label` | `member_resolution=cycle_ref` |
| `[*]....Definitions[i].ConnectorData.*` | `building_connector` | — | Via variant import |

## Placement rule mappings

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.PlacementRequirements[]` | `building_placement_rule` | (row) |
| `[*]....PlacementRequirements[i].$type` | `building_placement_rule` | `rule_kind` (mapped enum) |

## Backing-field / runtime paths (no domain column)

| JSON path | Classification |
| --------- | -------------- |
| `[*].simulation_parameters.<*k__BackingField>` | runtime metadata |
| `[*].definition_snapshot.<*k__BackingField>` | runtime metadata |
| `[*].definition_snapshot.Title` with `$cycle` | runtime metadata |
| `[*].definition_snapshot._Definitions` | duplicate of `Definitions` — use `Definitions` only |

## Sibling file mappings

| Sibling path | Target | Link |
| ------------ | ------ | ---- |
| `buildings.json[*]` same `source_guid` | `building` canonical snapshot | `snapshot_content_hash` must match |
| `building_variants.json[*].Id.Name` | `building_variant` | `building_group_member.building_variant_id` |
| `manifest.file_hashes["building_groups.json"]` | `game_data_import_batch` | `file_hash` |
