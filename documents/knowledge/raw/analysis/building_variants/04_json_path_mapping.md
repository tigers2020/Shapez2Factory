# JSON Path Mapping — `building_variants.json`

## Envelope

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[*]` | Variant row | domain entity | `building_variant` | (row) | — | 131 rows |
| `[*].stable_id` | Variant hash | domain entity (id) | `building_variant` | `stable_id` | unique | |
| `[*].source_guid` | Internal name copy | entity attribute | `building_variant` | `internal_name` | redundant | Same as Id.Name |
| `[*].display_name_key` | Display key | entity attribute | `building_variant` | `display_name_key` | | |
| `[*].building_stable_id` | Parent building FK | relationship | `building_variant` | `building_group_id` | nullable | Always empty |
| `[*].source_type_name` | Dump label | source metadata | audit | — | | |
| `[*].source_path` | Unity path | source metadata | — | — | | empty |
| `[*].definition_snapshot.Id.Name` | Canonical name | domain entity key | `building_variant` | `internal_name` | unique | |
| `[*].definition_snapshot` | Full graph | domain payload | (parsed children) | `snapshot_content_hash` | | Not stored as blob |

## Connector mappings

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.ConnectorData.AllBuildingConnectors[]` | `building_connector` | (row) |
| `[*]....AllBuildingConnectors[i].$type` | `building_connector` | `connector_role` |
| `[*]....AllBuildingConnectors[i].TileDirection.Value` | `building_connector` | `tile_direction` |
| `[*]....AllBuildingConnectors[i].IOType` | `building_connector` | `io_channel_type` |
| `[*]....AllBuildingConnectors[i].StandType` | `building_connector` | `stand_type` |
| `[*]....AllBuildingConnectors[i].Seperators` | `building_connector` | `has_seperators` |
| `[*]....AllBuildingConnectors[i].Position_L.x/y/z` | `building_connector` | `position_*` |

## Footprint mappings

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.ConnectorData.TileDimensions.x/y/z` | `building_variant` | `size_x/y/z` |
| `[*].definition_snapshot.ConnectorData.Tiles[]` | `building_footprint_tile` | (row) |
| `[*]....Tiles[i].x/y/z` | `building_footprint_tile` | coords |

## Inferred mappings

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.Id.Name` ends with `Mirrored` | `building_variant` | `is_mirrored=true` |
| `len(AllBuildingConnectors)` | `building_variant` | `connector_count` |

## Runtime / audit only (no domain column)

| JSON path | Notes |
| --------- | ----- |
| `[*].definition_snapshot.<*k__BackingField>` | Strip |
| `[*].definition_snapshot.IEntityConnectorData<...>.AllConnectors` | Ignore duplicate |
| `[*].definition_snapshot.CustomData.$cycle` | Graph pointer |
| `[*].definition_snapshot.ConnectorData.LegacyBuildingIOMap` | Optional legacy table |
| 156 distinct `$type` values elsewhere in snapshot | custom config phase 2 |

## Sibling imports

| Sibling path | Usage |
| ------------ | ----- |
| `building_groups.json` → `Definitions[].Id.Name` | `building_group_member.building_variant_id` |
| `belts_pipes_transport.json` → snapshot `Id.Name` | verify hash against variant row |
| `manifest.file_hashes["building_variants.json"]` | import batch integrity |
