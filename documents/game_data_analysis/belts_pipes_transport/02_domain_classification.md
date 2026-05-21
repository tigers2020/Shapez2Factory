# Domain Classification — `belts_pipes_transport.json`

## Envelope layer (per array element)

| JSON field | Classification | Notes |
| ---------- | -------------- | ----- |
| `transport_kind` | **domain entity** (business key) | Planner/simulation label (9 values) |
| `stable_id` | **domain entity** (identifier) | Transport registry hash; not variant ID |
| `display_name_key` | **entity attribute** | i18n/display; equals `transport_kind` today |
| `source_guid` | **entity attribute** | Player-facing alias; equals `transport_kind` |
| `source_path` | **source metadata** | Always empty string |
| `source_type_name` | **source metadata** | Dump capture type `BuildingDefinition` |
| `definition_snapshot` | **relationship payload** | Canonical geometry lives here but **dedupe** to `building_variant` |

## Inferred envelope attributes (not separate JSON keys)

| Concept | Classification | Source |
| ------- | -------------- | ------ |
| `transport_category` | **enum / choice** (inferred) | `belt`, `belt_port`, `fluid_port`, `pipe`, `wire`, `signal_port` from `transport_kind` |
| `internal_variant_name` | **relationship** | `definition_snapshot.Id.Name` → `building_variant` |

---

## `definition_snapshot` (shared with `building_variants.json`)

| Path / field | Classification |
| ------------ | -------------- |
| `Id.Name` | **relationship** (variant FK) |
| `ConnectorData.AllBuildingConnectors[]` | **ordered child record** |
| `ConnectorData.AllBuildingConnectors[].TileDirection.Value` | **enum / choice** (`West`, `East`, …) |
| `ConnectorData.AllBuildingConnectors[].IOType` | **enum / choice** (`ElevatedBorder`, `Pipe`, `Wire`, `Building`, `None`) |
| `ConnectorData.AllBuildingConnectors[].StandType` | **enum / choice** (`Normal`, `None`, null) |
| `ConnectorData.AllBuildingConnectors[].Seperators` | **entity attribute** (bool; typo preserved from dump) |
| `ConnectorData.AllBuildingConnectors[].Position_L` | **entity attribute** (local pivot coords) |
| `ConnectorData.AllBuildingConnectors[].$type` | **runtime / reflection / debug metadata** → map to `connector_role` enum |
| `ConnectorData.Tiles[]` | **ordered child record** (footprint) |
| `ConnectorData.TileDimensions` | **entity attribute** |
| `ConnectorData.TileBounds` / `TileBoundsCenter` | **entity attribute** |
| `ConnectorData.LegacyBuildingIOMap` | **source metadata** + graph cycles (`$cycle`) |
| `CustomData` / `IEntityDefinition.CustomData` | **unknown / needs human review** (simulation/rendering config) |
| `IEntityConnectorData<...>.AllConnectors` | **runtime / reflection / debug metadata** (duplicate) |
| `<*k__BackingField>` | **runtime / reflection / debug metadata** |
| `$type` values like `Game.Content.*`, `System.Reflection.*`, `UnityEngine.*` | **runtime / reflection / debug metadata** |

---

## `$type` → domain enum mapping (connector roles only)

Serializer `$type` must **not** become Django model class names. Map to `connector_role`:

| `$type` (observed in connectors) | Proposed `connector_role` |
| -------------------------------- | ------------------------- |
| `BuildingItemInput` | `item_input` |
| `BuildingItemOutput` | `item_output` |
| `BuildingFluidInput` | `fluid_input` |
| `BuildingFluidOutput` | `fluid_output` |
| `BuildingFluidJunction` | `fluid_junction` |
| `BuildingSignalJunction` | `signal_junction` |
| `BuildingSignalInput` | `signal_input` |
| `BuildingSignalOutput` | `signal_output` |
| `BeltPortOutput` | `belt_port_output` |
| `BeltPortInput` | `belt_port_input` |

Other `$type` strings (e.g. `ConveyorConfiguration`, `WireMetaBuildingDefinition+DrawData`) belong in **custom simulation config** parsing or audit storage — **not** domain table names.

---

## Special rule compliance

Strings matching `Game.Content.*`, generic arity types, `Version=`, `#nnn` appear inside nested `$type` and property keys — classified as **runtime/reflection/debug metadata**, excluded from ORM model names.

---

## Unknown / needs human review

| Item | Why |
| ---- | --- |
| `CustomData.All[]` entries | Deep simulation/rendering; 60+ `$type` variants |
| `$cycle` in `LegacyBuildingIOMap` | Object graph serialization artifact |
| `_IOType` duplicate field | Redundant with `IOType` on some fluid connectors |
| Why transport `stable_id` ≠ variant `stable_id` with identical snapshot | Hash input may include envelope — confirm with dump tool |
| Link to `buildings.json` transport groups | No direct GUID match; mapping via variant/group TBD |
