# JSON Path Mapping — `buildings.json`

## Envelope

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ |
| `[*]` | Building group row | domain entity | `building` | (row) | — |
| `[*].stable_id` | Buildings registry hash | domain entity (id) | `building` | `stable_id` | unique |
| `[*].source_guid` | Group key | domain entity key | `building` | `group_key` | unique |
| `[*].display_name_key` | Plain label | entity attribute | `building` | `display_name_key` | |
| `[*].simulation_parameters` | Sim flags object | entity attribute | `building_simulation_setting` | (row) | 1:1 |
| `[*].definition_snapshot` | Group graph | domain payload | `building` | `snapshot_content_hash` | parsed |
| `[*].source_type_name` | Dump label | source metadata | audit | — | |
| `[*].source_path` | Empty path | source metadata | — | — | |

## Group snapshot attributes

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.Id.Id` | `building` | `group_key` (confirm) |
| `[*].definition_snapshot.IsTransportBuilding` | `building` | `is_transport_building` |
| `[*].definition_snapshot.DefaultPreferredPlacementMode` | `building` | `placement_mode` |
| `[*].definition_snapshot.PlayerBuildable` | `building` | `player_buildable` |
| `[*].definition_snapshot.AutoConnect` | `building` | `auto_connect` |

## Membership

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.Definitions[]` | `building_group_member` | (row) |
| `[*]....Definitions[i].Id.Name` | `building_group_member` | `internal_variant_name` |
| `[*]....Definitions[i].$cycle` | `building_group_member` | `cycle_label` |

## Placement rules

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.PlacementRequirements[]` | `building_placement_rule` | (row) |
| `[*]....PlacementRequirements[i].$type` | `building_placement_rule` | `rule_kind` |

## Sibling overlay (not in buildings.json)

| JSON path (`building_groups.json`) | Target table | Target column |
| ---------------------------------- | ------------ | ------------- |
| `[*].display_name_key` (LazyText) | `building_localization_overlay` | `title_lazy_key` |
| `[*].description_key` | `building_localization_overlay` | `description_lazy_key` |

## Runtime paths (no domain column)

| JSON path | Notes |
| --------- | ----- |
| `simulation_parameters.<*k__BackingField>` | Strip |
| `definition_snapshot.<*k__BackingField>` | Strip |
| `Icon.$unity` | Audit |
| `Title` / `Description` with `$cycle` | Resolve via localization pipeline |
