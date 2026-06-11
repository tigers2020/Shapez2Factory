# `research_unlocks.json` — deep structure

- **Bytes:** 1,700,238
- **Root:** `array[436]`
- **Rows:** 436
- **Unique norm paths:** 4709

## Row envelope (all rows)

| key | rows | rate |
| --- | ---: | ---: |
| `stable_id` | 436 | 1.0000 |
| `source_type_name` | 436 | 1.0000 |
| `source_guid` | 436 | 1.0000 |
| `source_path` | 436 | 1.0000 |
| `display_name_key` | 436 | 1.0000 |
| `definition_snapshot` | 435 | 0.9977 |
| `simulation_parameters` | 16 | 0.0367 |
| `manager_snapshot` | 1 | 0.0023 |
| `progression_layout` | 1 | 0.0023 |
| `research_config` | 1 | 0.0023 |

## `source_type_name` distribution

- `ResearchSideQuest` — 188
- `Game.Core.Research.ResearchUpgradeId` — 168
- `ResearchSideUpgrade` — 51
- `ResearchLevel` — 13
- `Game.Core.Research.ResearchMechanicId` — 4
- `ResearchUnlockManager` — 1
- `ResearchConfig` — 1
- `ResearchProgression` — 1
- `ResearchRewardSideUpgrade` — 1
- `ResearchLevel+Line` — 1
- `ResearchRewardMechanic` — 1
- `ResearchCostShapes` — 1
- `ResearchRewardResearchPoints` — 1
- `ResearchRewardIslandGroup` — 1
- `ResearchRewardBuildingGroup` — 1

## Artifacts

- [Merged schema](research_unlocks.schema.txt)
- [Path catalog](research_unlocks.paths.tsv)

## Longest paths (sample)

| depth | path |
| ----: | ---- |
| 8 | `manager_snapshot.Mode.Scenario.RailColorRegistry.RuntimeToSerialIds.Game.Core.Rails.RailColor` |
| 8 | `manager_snapshot.CostManager.ShapeStorage.ShapeAmountChangedHooks._OnChanged....(truncated)` |
| 8 | `manager_snapshot.CostManager.ShapeStorage.ShapeUnifier.DefinitionMappings....(truncated)` |
| 8 | `manager_snapshot.CostManager.ShapeStorage.ShapeDeliverHooks._OnChanged....(truncated)` |
| 8 | `manager_snapshot.CostManager.ShapeStorage.ShapeIdManager.HashLookup....(truncated)` |
| 8 | `manager_snapshot.CostManager.ShapeStorage.ShapeIdManager.IdLookup....(truncated)` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection.DataValidOnlyWhenSingleMatching` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection.DataValidOnlyWhenSingleMatching.$cycle` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IPresentationData.DataValidOnlyWhenSingleMatching` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IPresentationData.DataValidOnlyWhenSingleMatching.$cycle` |
| 7 | `definition_snapshot.SideUpgrades[].Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection` |
| 7 | `definition_snapshot.SideUpgrades[].Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IPresentationData` |
| 7 | `definition_snapshot.Levels[].Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection.Match` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].IslandDefinitions[].IEntityDefinition.CustomData` |
| 7 | `definition_snapshot.Levels[].Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IPresentationData` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IPresentationData.Match` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Description.PlaceholderResolver.Replacements` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].<Icon>k__BackingField.instance_id` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].<Icon>k__BackingField.$unity` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Title.PlaceholderResolver.Replacements` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Description.PlaceholderResolver.$type` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].<Icon>k__BackingField.name` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Description.Id.<Id>k__BackingField` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Title.PlaceholderResolver.$type` |
| 7 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Title.Id.<Id>k__BackingField` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Icon.instance_id` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Icon.$unity` |
| 7 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].Icon.name` |
| 7 | `manager_snapshot.UnlockProgressManager.Progression._UpgradesById....(truncated)` |
| 7 | `manager_snapshot.Mode.WikiDatabase._KnowledgePanelEntries....(truncated)` |
| 7 | `manager_snapshot.Mode.Buildings._DefinitionsById....(truncated)` |
| 7 | `manager_snapshot.Mode.Islands.DefinitionsById....(truncated)` |
| 7 | `manager_snapshot.Mode.WikiDatabase.Entries....(truncated)` |
| 6 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection.DataValidOnlyWhenSingleMatching` |
| 6 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IPresentationData.DataValidOnlyWhenSingleMatching` |
| 6 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].IslandDefinitions[].<Layout>k__BackingField` |
| 6 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.DataPerTypeCache.IslandGroupCollection` |
| 6 | `definition_snapshot.Rewards[].GroupDefinition.IIslandDefinitionGroup.CustomData.All[].<ShowAsReward>k__BackingField` |
| 6 | `definition_snapshot.GroupDefinition.IIslandDefinitionGroup.CustomData.All[].IslandDefinitions[].<Id>k__BackingField` |

