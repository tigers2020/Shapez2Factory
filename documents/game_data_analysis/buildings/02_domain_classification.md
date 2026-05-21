# Domain Classification — `buildings.json`

## Envelope

| JSON field | Classification |
| ---------- | -------------- |
| `source_guid` / `Id.Id` | **domain entity** (business key) |
| `stable_id` | **domain entity** (buildings-registry id) |
| `display_name_key` | **entity attribute** | Plain key (not LazyText in this file) |
| `simulation_parameters` (logical fields) | **entity attribute** |
| `simulation_parameters.<*k__BackingField>` | **runtime / reflection / debug metadata** |
| `source_type_name` | **source metadata** |
| `source_path` | **source metadata** |
| `definition_snapshot` | **domain payload** (parsed, not stored as blob) |

## Group-level snapshot fields

| Field | Classification |
| ----- | -------------- |
| `IsTransportBuilding` | **entity attribute** |
| `DefaultPreferredPlacementMode` | **enum / choice** |
| `PlayerBuildable`, `Selectable`, `Removable`, `AutoConnect`, … | **entity attribute** |
| `Title`, `Description` | **entity attribute** (localization objects) |
| `Icon` | **source metadata** (`$unity`) |
| `Definitions[]` | **ordered child record** (variant membership) |
| `PlacementRequirements[]` | **ordered child record** |
| `PlacementIndicatorTypes[]` | **ordered child record** |
| `StructureOverview`, `LinkedWikiEntry`, `RequiredStoreContentId` | **unknown / needs human review** |
| `<*k__BackingField>` keys | **runtime / reflection / debug metadata** |
| `$cycle` | **runtime / reflection / debug metadata** |

## `Definitions[]` members

| Shape | Classification |
| ----- | -------------- |
| `{ "Id": { "Name": "..." }, "ConnectorData": ... }` | **relationship** → `building_variant` |
| `{ "$cycle": "..." }` | **runtime metadata** (intra-graph ref) |

## `simulation_parameters` logical fields

| Field | Classification |
| ----- | -------------- |
| `IsTransportBuilding` | **entity attribute** |
| `PipetteOverrideId.Id` | **entity attribute** / optional FK |
| `ShowStatBeltProcessingTime` | **entity attribute** |
| `ShowStatBuildingsPerFullBelt` | **entity attribute** |
| `ShowInSpeedOverview` | **entity attribute** |

## Placement requirement `$type` values

Map to `placement_rule_kind` enum — **not** Django models named `BuildingNotOnHubChunkRequirement`, etc.

## Special rule

`BuildingDefinitionGroup` in `source_type_name` → **source metadata only**.

Generic `Game.Core.*` / `IEntity*` keys → **runtime/reflection**.
