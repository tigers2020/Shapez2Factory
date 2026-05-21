# JSON Path Mapping — `belts_pipes_transport.json`

## Envelope mappings (authoritative for this file)

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[*]` | Transport definition row | domain entity | `transport_building_registry` | (row) | — | 9 elements |
| `[*].stable_id` | Transport registry ID | domain entity (id) | `transport_building_registry` | `stable_id` | PK natural | ≠ variant `stable_id` |
| `[*].transport_kind` | Planner/sim identifier | domain entity key | `transport_building_registry` | `transport_kind` | unique | Used in `simulation_systems.json` |
| `[*].display_name_key` | Display/i18n | entity attribute | `transport_building_registry` | `display_name_key` | | Same as `transport_kind` |
| `[*].source_guid` | Player-facing alias | entity attribute | `transport_building_registry` | `player_facing_key` | | |
| `[*].source_path` | Unity path | source metadata | — | — | | Always `""` |
| `[*].source_type_name` | Dump type | source metadata | `game_data_import_batch` / audit | `dump_capture_type` | | `BuildingDefinition` |
| `[*].definition_snapshot.Id.Name` | Internal variant name | relationship | `building_variant` | `internal_name` | FK lookup | 9/9 match variants file |
| `[*].definition_snapshot` (whole) | Building graph | relationship payload | — | — | dedupe | Import via variant, not duplicated |

## Connector mappings (import via variant dedupe)

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship |
| --------- | ---------------- | -------------- | ------------ | ------------- | -------------- |
| `[*].definition_snapshot.ConnectorData.AllBuildingConnectors[]` | Connector list | ordered child | `building_connector` | (row) | → variant |
| `[*]....AllBuildingConnectors[i].TileDirection.Value` | Facing | enum | `building_connector` | `tile_direction` | |
| `[*]....AllBuildingConnectors[i].IOType` | Channel surface | enum | `building_connector` | `io_channel_type` | |
| `[*]....AllBuildingConnectors[i].StandType` | Stand style | enum | `building_connector` | `stand_type` | nullable |
| `[*]....AllBuildingConnectors[i].Seperators` | Separator flag | entity attribute | `building_connector` | `has_seperators` | typo from dump |
| `[*]....AllBuildingConnectors[i].Position_L.x/y/z` | Local position | entity attribute | `building_connector` | `position_*` | |
| `[*]....AllBuildingConnectors[i].$type` | Serializer discriminator | runtime metadata | `building_connector` | `connector_role` | mapped enum |
| `[*]....AllBuildingConnectors[i]._IOType` | Duplicate IO | unknown | — | — | review / ignore |

## Footprint mappings

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].definition_snapshot.ConnectorData.Tiles[]` | `building_footprint_tile` | (row) |
| `[*].definition_snapshot.ConnectorData.Tiles[i].x/y/z` | `building_footprint_tile` | `x`, `y`, `z` |
| `[*].definition_snapshot.ConnectorData.TileDimensions.x/y/z` | `building_variant` | `size_x/y/z` | inferred |

## Legacy / reflection paths (audit only)

| JSON path | Classification | Target | Notes |
| --------- | -------------- | ------ | ----- |
| `[*].definition_snapshot.ConnectorData.LegacyBuildingIOMap.*` | source metadata | import audit graph | Contains `$cycle` |
| `[*].definition_snapshot.IEntityConnectorData<...>.AllConnectors` | runtime metadata | — | Duplicate of connectors |
| `[*].definition_snapshot.<*k__BackingField>` | runtime metadata | — | Strip on import |
| `[*].definition_snapshot.CustomData.All[]` | unknown | `building_variant_custom_config` or audit | Deferred |

## Inferred envelope column

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `[*].transport_kind` (lookup table) | `transport_building_registry` | `transport_category` |

| `transport_kind` | `transport_category` |
| ---------------- | ---------------------- |
| `ForwardBelt` | `belt` |
| `BeltPortSender` / `BeltPortReceiver` | `belt_port` |
| `FluidPortSender` / `FluidPortReceiver` | `fluid_port` |
| `PipeForward` | `pipe` |
| `WireForward` | `wire` |
| `WireTransmitterSender` / `WireTransmitterReceiver` | `signal_port` |

## Manifest

| JSON path | Target table | Target column |
| --------- | ------------ | ------------- |
| `manifest.file_hashes["belts_pipes_transport.json"]` | `game_data_import_batch` | `file_hash` |
