# Domain Classification — `toolbar_entries.json`

## Envelope

| Path | Classification |
| ---- | -------------- |
| `stable_id` | source metadata (unique) |
| `source_type_name` | enum / choice → `element_kind` |
| `display_name_key` | entity attribute (**tree_path**) |
| `source_path` | source metadata (often empty) |
| `source_guid` | source metadata |
| `simulation_parameters` | source metadata |
| `definition_snapshot` | mixed domain + runtime |

## Building placement snapshot

| Path | Classification |
| ---- | -------------- |
| `BuildingDefinition.Id.Id` | entity attribute → FK key to buildings |
| `BuildingDefinition.IsTransportBuilding` | entity attribute |
| `BuildingDefinition.PlayerBuildable` | entity attribute |
| `BuildingDefinition.Icon.name` | relationship → `sprite_asset` |
| `BuildingDefinition.Title` | unknown (LazyLocalizedText) |
| `IPlacementToolbarElementData.PlacerId` | entity attribute |
| `IPresentableToolbarElementData.*` | source metadata naming |

## Island placement

| Path | Classification |
| ---- | -------------- |
| `IslandGroup.Id.Name` | entity attribute |
| `SectionIndex` | entity attribute |

## Group / category

| Path | Classification |
| ---- | -------------- |
| `Children[]` | ordered child record (in-row; also flattened as separate elements) |
| `MechanicRequiredToUnlock.Id` | relationship → `research_mechanic` |
| `RememberPreferredChild` | entity attribute |

## Runtime-only

| Path | Classification |
| ---- | -------------- |
| `$type`, `$unity`, `instance_id` | source/runtime metadata |
| `LazyLocalizedText` `$cycle` | source metadata |
| Interface field names as DB columns | forbidden |

## Entity

**Toolbar element** (UI placement tree node), not “ToolbarElementData” CLR class.
