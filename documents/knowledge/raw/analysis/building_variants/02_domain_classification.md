# Domain Classification — `building_variants.json`

## Envelope layer

| JSON field | Classification | Notes |
| ---------- | -------------- | ----- |
| `stable_id` | **domain entity** (identifier) | Variant registry hash |
| `source_guid` | **entity attribute** | Redundant with `Id.Name` in dump |
| `display_name_key` | **entity attribute** | Same as internal name today |
| `building_stable_id` | **relationship** (nullable FK) | Always empty — parent group/building link not populated |
| `source_path` | **source metadata** | Empty |
| `source_type_name` | **source metadata** | `BuildingDefinition` — not ORM model |
| `definition_snapshot` | **domain payload** | Parsed into child tables |

---

## `definition_snapshot.Id`

| Field | Classification |
| ----- | -------------- |
| `Id.Name` | **domain entity** key (`internal_variant_name`) |

---

## `ConnectorData`

| Path | Classification |
| ---- | -------------- |
| `AllBuildingConnectors[]` | **ordered child record** |
| `AllBuildingConnectors[].TileDirection.Value` | **enum / choice** (`West`, `East`, `North`, `South`, `Up`, `Down`) |
| `AllBuildingConnectors[].IOType` | **enum / choice** |
| `AllBuildingConnectors[].StandType` | **enum / choice** / nullable |
| `AllBuildingConnectors[].Seperators` | **entity attribute** (bool) |
| `AllBuildingConnectors[].Position_L.{x,y,z}` | **entity attribute** |
| `AllBuildingConnectors[].$type` | **runtime metadata** → `connector_role` enum |
| `AllBuildingConnectors[]._IOType` | **unknown / needs human review** (duplicate) |
| `Tiles[]` | **ordered child record** |
| `TileDimensions` | **entity attribute** |
| `TileBounds`, `TileBoundsCenter` | **entity attribute** |
| `LegacyBuildingIOMap` | **source metadata** + graph (`$cycle`) |

### Observed `IOType` values

`Building`, `ElevatedBorder`, `Regular`, `Pipe`, `Wire`, `None`

### Observed connector `$type` → domain `connector_role`

| `$type` | `connector_role` |
| ------- | ---------------- |
| `BuildingItemInput` | `item_input` |
| `BuildingItemOutput` | `item_output` |
| `BuildingFluidInput` | `fluid_input` |
| `BuildingFluidOutput` | `fluid_output` |
| `BuildingFluidJunction` | `fluid_junction` |
| `BuildingSignalInput` | `signal_input` |
| `BuildingSignalOutput` | `signal_output` |
| `BuildingSignalJunction` | `signal_junction` |
| `BeltPortInput` | `belt_port_input` |
| `BeltPortOutput` | `belt_port_output` |

---

## `CustomData` / simulation config

| Path | Classification |
| ---- | -------------- |
| `CustomData` with only `$cycle` | **runtime / reflection / debug metadata** |
| `IEntityDefinition.CustomData` | **unknown / needs human review** |
| Deep `$type` nodes (`ConveyorConfiguration`, `+*+DrawData`, etc.) | **runtime metadata** — parse in phase 2, not as 156 tables |

---

## Inferred domain attributes (not top-level JSON keys)

| Concept | Classification | Inference |
| ------- | -------------- | --------- |
| `is_mirrored_variant` | **entity attribute** | `Id.Name` ends with `Mirrored` |
| `footprint_size` | **entity attribute** | from `TileDimensions` |
| `connector_count` | **entity attribute** | derived |

---

## Special rule compliance

Generic property keys (`IEntityConnectorData<Game.Core.Coordinates...>`) and `$type` values containing `Game.Content`, `System.Reflection`, `UnityEngine` → **runtime/reflection/debug metadata**.

---

## Unknown / needs human review

| Item | Question |
| ---- | -------- |
| Empty `building_stable_id` | Populate later from group membership import? |
| `LabelDefaultInternalVariant` with 0 connectors | Valid building or dump omission? |
| Full CustomData expansion | Required for simulation parity? |
| Mirrored vs non-mirrored pairs | Explicit `mirrored_from_variant_id` FK? |
