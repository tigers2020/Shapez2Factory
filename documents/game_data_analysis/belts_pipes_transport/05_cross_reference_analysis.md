# Cross-Reference Analysis — `belts_pipes_transport.json`

## FK relationships (resolved)

| From | To | Cardinality | Evidence |
| ---- | -- | ----------- | -------- |
| `transport_building_registry.building_variant_id` | `building_variant` via `Id.Name` | 9 : 1 | Snapshot JSON identical for all 9 |
| `building_connector.building_variant_id` | `building_variant` | N : 1 | 13 connectors total across file |
| `building_footprint_tile.building_variant_id` | `building_variant` | N : 1 | 9 tiles |

## FK relationships (transport ID namespace)

| From | To | Status |
| ---- | -- | ------ |
| `transport_building_registry.stable_id` | `building_variant.stable_id` | **Different hashes** (0/9 equal) — parallel registries |
| `transport_building_registry.stable_id` | other `game_data` files | **No** string hits in buildings/items/prefabs |

## M2M relationships

**None** in envelope. Connectors are ordered children, not M2M.

## Ordered child relationships

```text
transport_building_registry
  └─ references → building_variant (by internal_name)
        ├─ has many → building_connector (ordered by array index)
        └─ has many → building_footprint_tile (ordered)
```

## Inferred references by name (not hash)

| Transport `transport_kind` | `Id.Name` (variant) | Category |
| -------------------------- | ------------------- | -------- |
| `ForwardBelt` | `BeltDefaultForwardInternalVariant` | belt |
| `BeltPortSender` | `BeltPortSenderInternalVariant` | belt_port |
| `BeltPortReceiver` | `BeltPortReceiverInternalVariant` | belt_port |
| `FluidPortSender` | `FluidPortSenderInternalVariant` | fluid_port |
| `FluidPortReceiver` | `FluidPortReceiverInternalVariant` | fluid_port |
| `PipeForward` | `PipeForwardInternalVariant` | pipe |
| `WireForward` | `WireDefaultForwardInternalVariant` | wire |
| `WireTransmitterSender` | `WireTransmitterSenderInternalVariant` | signal_port |
| `WireTransmitterReceiver` | `WireTransmitterReceiverInternalVariant` | signal_port |

## Unresolved references

| Reference | Status | Notes |
| --------- | ------ | ----- |
| `source_guid` → `buildings.json` | **Unresolved** | Transport uses `ForwardBelt`; buildings use `BeltDefaultVariant` groups |
| `building_variant.building_stable_id` | **Empty** in variants | All 9 matched variants have `building_stable_id: ""` |
| Toolbar → transport | **Partial** | String mentions in `toolbar_entries.json`; uses `BuildingDefinitionGroup` |
| Simulation → transport | **Observed** | All 9 kinds appear in `simulation_systems.json` text |

## Source metadata references

| Signal | Role |
| ------ | ---- |
| `source_type_name: BuildingDefinition` | Dump label only |
| `$type` (60 values) | Serializer / reflection |
| `$cycle` in LegacyBuildingIOMap | Graph serialization |
| Empty `source_path` | Placeholder from reflection export |

## Relationship diagram

```text
game_data_import_batch
  └─ has many → transport_building_registry (9)
        └─ references → building_variant (9 internal names)
              ├─ has many → building_connector (13)
              └─ has many → building_footprint_tile (9)

building (buildings.json, IsTransportBuilding=true)
  └─ has many → building_variant (other variants; link to transport TBD)
       └─ NOT directly keyed by transport_kind today

simulation_system
  └─ references by name → transport_kind (textual; FK TBD)

toolbar_entry
  └─ references by name → subset of transport_kind / variant titles
```

## Duplicate data warning

```text
belts_pipes_transport.json[*].definition_snapshot
  ≡ (byte equal) building_variants.json[matching Id.Name].definition_snapshot
```

Import pipeline must **not** create drift between two copies.
