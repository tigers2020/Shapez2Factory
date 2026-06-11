# Domain Classification — `building_groups.json`

## Envelope layer

| JSON field | Classification | Notes |
| ---------- | -------------- | ----- |
| `stable_id` | **domain entity** (identifier) | Group-registry hash; separate from `buildings.json` |
| `source_guid` | **domain entity** (business key) | e.g. `CutterDefaultVariant` |
| `display_name_key` | **entity attribute** | Localization reference (`LazyText[...]`) |
| `description_key` | **entity attribute** | Localization reference |
| `simulation_parameters` | **entity attribute** (structured) | Planner/sim UI flags |
| `simulation_parameters.<*k__BackingField>` | **runtime / reflection / debug metadata** | Duplicate of logical fields |
| `source_path` | **source metadata** | Always empty |
| `source_type_name` | **source metadata** | `BuildingDefinitionGroup` — not ORM model name |
| `definition_snapshot` | **relationship payload** | Dedupe with `buildings.json`; parse children once |

---

## `definition_snapshot` (group-level)

| Path / field | Classification |
| ------------ | -------------- |
| `Id.Id` | **domain entity** key | Equals `source_guid` |
| `Title` / `Description` | **entity attribute** | Lazy localization objects |
| `Icon` | **source metadata** | Unity sprite ref (`$unity`, `instance_id`) |
| `IsTransportBuilding` | **entity attribute** (bool) | 12 true |
| `DefaultPreferredPlacementMode` | **enum / choice** | Placement policy |
| `PlayerBuildable`, `Selectable`, `Removable` | **entity attribute** | All true in dump |
| `AutoConnect`, `AutoRotateToFitStructures`, … | **entity attribute** | Placement/sim behavior flags |
| `Definitions[]` | **ordered child record** | Variant membership |
| `PlacementRequirements[]` | **ordered child record** | Placement rules |
| `PlacementIndicatorTypes[]` | **ordered child record** | UI/placement indicators |
| `StructureOverview` | **unknown / needs human review** | Slots/video overview |
| `PipetteOverrideId`, `RequiredStoreContentId`, `LinkedWikiEntry` | **entity attribute** / FK-like ids |
| `<Title>k__BackingField`, `<Icon>k__BackingField`, … | **runtime / reflection / debug metadata** |
| `$cycle` on Title/Description/StructureOverview | **runtime / reflection / debug metadata** | Graph pointer |

### `DefaultPreferredPlacementMode` values

| Value | Count |
| ----- | ----- |
| `CodeOverriden` | 19 |
| `LinePerpendicular` | 18 |
| `Single` | 17 |
| `Area` | 11 |
| `LineBoth` | 1 |
| `LineParallel` | 1 |

---

## `Definitions[]` members

| Member shape | Classification |
| ------------ | -------------- |
| Full object with `Id.Name` + `ConnectorData` | **relationship** + embedded variant payload → FK `building_variant` |
| `{"$cycle": "<label>"}` only | **runtime / reflection / debug metadata** | Resolve to prior embedded member in import graph |
| `Definitions[].$type: BuildingDefinition` | **runtime metadata** → member is variant definition |
| `ConnectorData.*` | Same as `building_variants` analysis (connectors, tiles) |

---

## `simulation_parameters` (logical fields only)

| Field | Classification |
| ----- | -------------- |
| `IsTransportBuilding` | **entity attribute** (bool) |
| `PipetteOverrideId` | **entity attribute** / optional FK (`Id` string, often empty) |
| `ShowStatBeltProcessingTime` | **entity attribute** |
| `ShowStatBuildingsPerFullBelt` | **entity attribute** |
| `ShowInSpeedOverview` | **entity attribute** |

---

## `PlacementRequirements[]` `$type` values (observed)

| `$type` | Classification |
| ------- | -------------- |
| `BuildingNotOnHubChunkRequirement` | **enum / choice** → `placement_rule_kind` |
| `PortReceiverValidNotchRotationRequirement` | **enum / choice** |
| `PortSenderValidNotchRotationRequirement` | **enum / choice** |
| `OnlyOnGroundLayerRequirement` | **enum / choice** |
| `CatapultOnHubBorderRequirement` | **enum / choice** |
| `OnlyOnShapeResourcePatchPlacementRequirement` | **enum / choice** |
| `OnlyOnFluidResourcePatchPlacementRequirement` | **enum / choice** |
| `NotNextToResourcePatchRequirement` | **enum / choice** |

---

## Special rule compliance

No `Game.Content.*` **values** as primary keys; generic names appear as JSON **property keys** (e.g. long `IEntity...` keys) → **runtime/reflection**, stripped on import.

`BuildingDefinitionGroup` in `source_type_name` → **source metadata only**.

---

## Unknown / needs human review

| Item | Question |
| ---- | -------- |
| Why duplicate file if identical to `buildings.json` snapshot | Separate `stable_id` + LazyText + `simulation_parameters` purpose |
| `$cycle` Definitions members | Importer must resolve to embedded variant ordinal |
| `StructureOverview.Slots` | Planner relevance vs wiki-only |
| `RequiredStoreContentId` | Link to store/ DLC content table? |
| 34 cycle-only members vs 97 embedded | Confirm cycle targets always earlier in same `Definitions` array |
