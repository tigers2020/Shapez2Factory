# `simulation_systems.json` — deep structure

- **Bytes:** 38,111,900
- **Root:** `array[180]`
- **Rows:** 180
- **Unique norm paths:** 47104

## Row envelope (all rows)

| key | rows | rate |
| --- | ---: | ---: |
| `stable_id` | 180 | 1.0000 |
| `source_type_name` | 180 | 1.0000 |
| `source_guid` | 180 | 1.0000 |
| `source_path` | 180 | 1.0000 |
| `display_name_key` | 180 | 1.0000 |
| `definition_snapshot` | 180 | 1.0000 |
| `simulation_parameters` | 175 | 0.9722 |

## `source_type_name` distribution

- `AtomicStatefulIslandSimulationSystem`2[[Game.Content.AtomicIslands.Conveyors.SpaceConveyorSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Game.Content.AtomicIslands.Conveyors.SpaceConveyorSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 38
- `Game.Content.AtomicIslands.Converters.SpaceConverterSystem` — 18
- `AtomicStatefulBuildingSimulationSystem`2[[BeltLift1LayerSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Lift1LayerSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 8
- `AtomicStatefulBuildingSimulationSystem`2[[BeltLift2LayerSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Lift2LayerSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 8
- `AtomicStatefulIslandSimulationSystem`2[[Game.Content.AtomicIslands.Splitter.SpaceSplitterSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Game.Content.AtomicIslands.Splitter.SpaceSplitterSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 8
- `AtomicStatefulIslandSimulationSystem`2[[Game.Content.AtomicIslands.Mergers.SpaceMergerSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Game.Content.AtomicIslands.Mergers.SpaceMergerSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 8
- `AtomicStatefulBuildingSimulationSystem`2[[Virtual2In1OutSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Virtual2InSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 6
- `AtomicStatefulBuildingSimulationSystem`2[[DisplaySimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[DisplaySimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 5
- `AtomicStatefulBuildingSimulationSystem`2[[MergerSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[MergerSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 4
- `AtomicStatefulBuildingSimulationSystem`2[[Virtual1In2OutSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Virtual1InSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 4
- `AtomicStatefulBuildingSimulationSystem`2[[Virtual1In1OutSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[Virtual1InSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 4
- `AtomicStatefulBuildingSimulationSystem`2[[RotatorSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[RotatorSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 3
- `AtomicStatefulBuildingSimulationSystem`3[[StackerSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[StackerSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[IStackerConfiguration, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 3
- `AtomicStatefulBuildingSimulationSystem`2[[FullCutterSimulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[FullCutterSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 2
- `AtomicStatefulBuildingSimulationSystem`2[[Splitter1To2Simulation, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null],[PrioritySplitterSimulationState, Game.Content, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null]]` — 2

## Artifacts

- [Merged schema](simulation_systems.schema.txt)
- [Path catalog](simulation_systems.paths.tsv)

## Longest paths (sample)

| depth | path |
| ----: | ---- |
| 17 | `definition_snapshot.TrainIslands.Production.FillerCargoFactory.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Production.ShapeCargoFactory.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Production.FluidCargoFactory.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Production.FillerCargoFactory.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Production.ShapeCargoFactory.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Production.FluidCargoFactory.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Navigation.QuickStation.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Navigation.WaitStation.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Navigation.QuickStation.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Navigation.WaitStation.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Navigation.Launcher.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Navigation.Catcher.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Navigation.Twister.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 17 | `definition_snapshot.TrainIslands.Navigation.Launcher.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Navigation.Catcher.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 17 | `definition_snapshot.TrainIslands.Navigation.Twister.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 16 | `definition_snapshot._HubIslands[].Definition.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors[]` |
| 16 | `definition_snapshot._HubIslands[].Definition.IEntityDefinition.CustomData.All[].IEntityConnectorData<Game.Core.Coordinates.LocalChunkPivot,Game.Core.Coordinates.ChunkVector,Game.Core.Coordinates.ChunkDirection>.AllConnectors` |
| 16 | `definition_snapshot.CargoExchanger.ShapeCargoLoaderUnloader.TrainsWagonCargoSimulator.WagonCargoFactoryTypeMap.Game.Core.Trains.LayeredWagonCargo`1[Game.Core.Trains.CargoContainer`1[Game.Content.Features.Fluids.FluidId]].Id` |
| 15 | `definition_snapshot.CargoExchanger.ShapeCargoLoaderUnloader.TrainsWagonCargoSimulator.WagonCargoFactoryTypeMap.Game.Core.Trains.LayeredWagonCargo`1[Game.Core.Trains.CargoContainer`1[Game.Content.Features.Fluids.FluidId]]` |
| 14 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Islands.Hub.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Islands.PlayingField.DrawPlayingFieldFlag` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.WireTransmitterReceiver.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.WireTransmitterSender.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.BeltPortReceiver.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.BeltPortSender.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.ForwardBelt.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.PipeForward.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.WireForward.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.Interlock.ResearchUnlockManager.Mode.Buildings.ShapeMiner.IEntityDefinition.CustomData.DataPerTypeCache.Game.Core.Rendering.Buildings.BuildingSimpleAnimationDrawer+Data` |
| 13 | `definition_snapshot.TrainIslands.Production.FillerCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpaceBeltOutputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.FillerCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpacePipeOutputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.ShapeCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpaceBeltOutputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.ShapeCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpacePipeOutputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.FluidCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpaceBeltOutputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.FluidCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpacePipeOutputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.FillerCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpaceBeltInputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.FillerCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpacePipeInputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.ShapeCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpaceBeltInputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.ShapeCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpacePipeInputConnector[]` |
| 13 | `definition_snapshot.TrainIslands.Production.FluidCargoFactory.IEntityDefinition.CustomData.All[].IslandIoMap.Game.Content.Features.SpacePaths.IslandIO.SpaceBeltInputConnector[]` |

