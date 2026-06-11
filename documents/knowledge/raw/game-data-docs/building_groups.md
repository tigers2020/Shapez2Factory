# `building_groups.json` — deep structure

- **Bytes:** 13,033,263
- **Root:** `array[67]`
- **Rows:** 67
- **Unique norm paths:** 2286

## Diff vs `buildings.json`

**2285 paths identical** under `definition_snapshot` / `simulation_parameters`.  
Additional envelope path unique to this file: **`description_key`** (string, 67/67).

## Row envelope (all rows)

| key | rows | rate |
| --- | ---: | ---: |
| `stable_id` | 67 | 1.0000 |
| `source_type_name` | 67 | 1.0000 |
| `source_guid` | 67 | 1.0000 |
| `source_path` | 67 | 1.0000 |
| `display_name_key` | 67 | 1.0000 |
| `definition_snapshot` | 67 | 1.0000 |
| `simulation_parameters` | 67 | 1.0000 |
| `description_key` | 67 | 1.0000 |

## `source_type_name` distribution

- `BuildingDefinitionGroup` — 67

## Artifacts

- [Merged schema](building_groups.schema.txt)
- [Path catalog](building_groups.paths.tsv)

## Longest paths (sample)

| depth | path |
| ----: | ---- |
| 11 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].Game.Content.BuildingPath.Simulation.IConveyorConfiguration.ConveyorSpeed.StepsPerTick` |
| 11 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].Game.Content.BuildingPath.Simulation.IConveyorConfiguration.ConveyorSpeed.ResearchId` |
| 11 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].Game.Content.BuildingPath.Simulation.IConveyorConfiguration.ConveyorSpeed.BaseSpeed` |
| 11 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].Game.Content.BuildingPath.Simulation.IConveyorConfiguration.ConveyorSpeed.$type` |
| 10 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data.DataValidOnlyWhenSingleMatching` |
| 10 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data.Match` |
| 10 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].Game.Content.BuildingPath.Simulation.IConveyorConfiguration.ConveyorSpeed` |
| 9 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.DataPerTypeCache.Core.Factory.IFactory`1[IBuildingConfiguration].DataValidOnlyWhenSingleMatching.$cycle` |
| 9 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration.ProvidingConfiguration.IProvidingFluidContainerConfiguration.ProvidingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration.ConsumingConfiguration.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration.ProvidingConfiguration.IProvidingFluidContainerConfiguration.ProvidingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration.ConsumingConfiguration.IConsumingFluidContainerConfiguration.ConsumingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration.LaunchConfiguration.IFluidPortLaunchConfiguration.MaxLaunchesPerMinute` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortReceiverConfiguration.LaunchConfiguration.IFluidPortLaunchConfiguration.PackageSizeInLiters` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration.LaunchConfiguration.IFluidPortLaunchConfiguration.MaxLaunchesPerMinute` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidPortSenderConfiguration.LaunchConfiguration.IFluidPortLaunchConfiguration.PackageSizeInLiters` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].ICrystalGeneratorConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidStorageConfiguration.ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidStorageConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidStorageConfiguration.ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IFluidStorageConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IPipeGateConfiguration.ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IPipeGateConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IPainterConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.DataPerTypeCache.Core.Factory.IFactory`1[IBuildingConfiguration].DataValidOnlyWhenSingleMatching` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IPipeGateConfiguration.ContainerConfig.IProvidingFluidContainerConfiguration.ProvidingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IPipeGateConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.ChamberConfig.IProvidingFluidContainerConfiguration.ProvidingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.ChamberConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IPainterConfiguration.ContainerConfig.IConsumingFluidContainerConfiguration.ConsumingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.OutputConfig.IProvidingFluidContainerConfiguration.ProvidingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.OutputConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.InputConfig.IProvidingFluidContainerConfiguration.ProvidingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.InputConfig.IConsumingFluidContainerConfiguration.ConsumingPriority` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.ChamberConfig.IProvidingFluidContainerConfiguration.ProvidingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.ChamberConfig.IConsumingFluidContainerConfiguration.ConsumingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.OutputConfig.IProvidingFluidContainerConfiguration.ProvidingRate` |
| 8 | `definition_snapshot.Definitions[].IEntityDefinition.CustomData.All[].IMixerConfiguration.OutputConfig.IConsumingFluidContainerConfiguration.ConsumingRate` |

