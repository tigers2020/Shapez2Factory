# Django Model Mapping

**Import metadata:** canonical logical names → Django classes — see [`_audit/10_import_metadata_unification.md`](../_audit/10_import_metadata_unification.md).  
Do **not** add `GameDataImportRun`, `GameDataSourceFile`, etc. in parallel.

| Django model | Canonical name | Purpose | Source reports | Source JSON paths | Cross references | Notes |
| ------------ | -------------- | ------- | -------------- | ----------------- | ---------------- | ----- |
| `ImportBatch` | `game_data_import_batch` | Import **run** / manifest header | manifest, all | `manifest.json` root | → all tables | UK: `manifest_self_hash` |
| `ArtifactChecksum` | `game_data_artifact_checksum` | Per **file** SHA gate | manifest | `file_hashes.*` | → batch | Not `SourceObject` |
| `ExportWarning` | Export caveats | manifest | `warnings[]` | → batch | |
| `ExportIncompleteSection` | Failed sections | manifest, translations | `incomplete_sections[]` | → batch | |
| `LocalizationExportStatus` | Empty l10n export | translations | `translations.json` + manifest | → batch | 1:1 batch |
| `SourceObject` | `source_object_record` | Row provenance | all planned | `[i]` envelope | → batch; optional `source_path` (auxiliary) | UK: `(batch, file, row_index)` |
| `UnknownProperty` | `unknown_property` | Ignored / unmapped keys | all planned | any | → batch | preview + `reason_code`; not `GameDataIgnoredField` |
| `GameContentAsset` | Merged prefab/sprite/material | prefabs, sprites, materials, asset_references | `[*].{stable_id,*_path}` | ← meta | `content_kind` enum |
| `AssetMetaReference` | Meta → content bridge | asset_references | `[*].ref_stable_id` | → `GameContentAsset` | |
| `FluidColor` | Paint palette | fluids | `definition_snapshot.Color.name` | ← shape slots | UK: `color_name` |
| `ShapeComponentKind` | Subpart lookup | items, shapes | `Parts[].Shape.name` | ← slots | |
| `ShapeRecipe` | Shape code header | shapes, items | `Hash`, `UniqueOperationId` | → layers | UK: `operation_uid`, `shape_hash` |
| `ShapeRecipeLayer` | Layer stack | shapes, items | `Layers[]` | → recipe | `order_index` |
| `ShapeQuadrantSlot` | Quadrant fill | shapes, items | `Parts[]` | → layer, kinds, fluid | |
| `BuildingVariant` | Internal geometry | building_variants | `definition_snapshot.Id.Name` | connectors, tiles | UK: `internal_name` |
| `BuildingConnector` | IO endpoints | building_variants | `AllBuildingConnectors[]` | → variant | `order_index` |
| `BuildingFootprintTile` | Occupied tiles | building_variants | `Tiles[]` | → variant | |
| `BuildingGroup` | Unified buildable family | buildings, building_groups | `source_guid` | members, rules | `display_profile` |
| `BuildingLocalizationOverlay` | LazyText keys | building_groups | `display_name_key` | → group | |
| `BuildingSimulationSetting` | Sim/UI flags | buildings, building_groups | `simulation_parameters` | → group | 1:1 |
| `BuildingGroupMember` | Variant membership | buildings, building_groups | `Definitions[]` | → variant | `order_index` |
| `BuildingPlacementRule` | Placement rules | building_groups | `PlacementRequirements[]` | → group | |
| `TransportBuildingRegistry` | Transport kinds | belts_pipes_transport | `transport_kind` | → variant | no variant re-import |
| `ResearchUpgrade` | Upgrade registry | research_unlocks | `ResearchUpgradeId` | prereqs, belt policy | UK: `upgrade_key` |
| `ResearchMechanic` | Mechanic gates | research_unlocks | `ResearchMechanicId` | prereqs | |
| `ResearchMilestone` | Main ladder | research_unlocks | `ResearchLevel` | costs | |
| `ResearchSideQuest` | Side quests | research_unlocks | `ResearchSideQuest` | costs | |
| `ResearchSideUpgrade` | Branch upgrades | research_unlocks | `ResearchSideUpgrade` | | |
| `ResearchUnlockCost` | Shape payment | research_unlocks | `Costs[].ShapeHash` | → `ShapeRecipe` | FK resolved |
| `ResearchPrerequisite` | Dependencies | research_unlocks | `RequiredUpgrades` / `RequiredMechanics` | upgrade/mechanic FK | imported for milestones & side quests |
| `ResearchGlobalConfig` | Global tunables | research_unlocks | manager row | batch | placeholder |
| `SimulationSystem` | Sim registration (180 rows) | simulation_systems | `simulation_parameters` | profile FK, types | UK `(batch, source_stable_id)` |
| `SimulationProfile` | Profile keys | detected signature | — | no enum migration |
| `SimulationClrProvenance` | CLR `source_type_name` capture | `source_type_name` | — | not domain-queryable; was `ImportAudit` |
| `ConnectableSimulation` + children | Connectable graph | `ConnectableSimulations[]` | building_variant FK | `connectable_key` + signatures |
| `GlobalBeltSpeedPolicy` | Batch-global belt speed | simulation_systems | `BeltSpeed` row | → `ResearchUpgrade` | synced from buffable |
| `SimulationBuffableSpeed` | `BuffableBeltSpeed` | simulation_systems | per param key | → `ResearchUpgrade` | |
| `SimulationMultipleBeltSpeed` | `MultipleBeltSpeed` | simulation_systems | `JumpSpeed` | → `SimulationBuffableSpeed` | |
| `SimulationRuntimeAuditIssue` | Converter/runtime audit rows | simulation_systems | converter profile | → `SimulationSystem` | enum `issue_code` / `severity`; no JSONField |
| `GameDataNamespace` / `GameDataSection` | Admin menu taxonomy only | — | — | — | maps `verbose_name_plural` → sections; **not** domain FKs |
| `GameDataReference` | Unresolved import refs (staging) | import pass | string targets | `from_source` → `SourceObject` | typed FK remains source of truth |
| `ToolbarTreeNode` | Toolbar structure | toolbar_entries | `display_name_key` (debug `tree_path`) | parent/child_index UK; `required_mechanic`; `icon_content_asset` | `source_object` FK |
| `ToolbarElement` | ACTION leaf only | toolbar_entries | placer rows | 1:1 `tree_node`, placements | 142 in current dump |
| `ToolbarBuildingPlacement` | Build action | toolbar_entries | `BuildingDefinition` | → `BuildingVariant` | resolves via Definitions[] |
| `ToolbarIslandPlacement` | Island action | toolbar_entries | `IslandGroup` | via `toolbar_element` | no `tree_path` on payload |
| `ClrTypeRegistryEntry` | CLR catalog | raw_type_index | `type_name`, `assembly_name` | optional validation | hashed `canonical_id` |
| `LocalizedMessage` | Resolved strings | translations | future `[*]` | all LazyText | empty dump |
