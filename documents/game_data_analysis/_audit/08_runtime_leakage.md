# Runtime Metadata Leakage Audit

Fields that must remain audit/source columns, not domain entities.

| Runtime field / pattern | Appears in | Risk | Recommendation |
| ----------------------- | ---------- | ---- | -------------- |
| `AtomicStatefulIslandSimulationSystem`2[[Game.Content…, Version=0.0.0.0, PublicKeyToken=null], …]` | simulation_systems | **CRITICAL** if promoted to entity | `simulation_system_entry.clr_type_audit` TEXT only |
| `Game.Core.Research.ResearchUpgradeId` | research_unlocks | **HIGH** | Row discriminator → `element_kind`; table `research_upgrade` |
| `BuildingBasedPlacementToolbarElementData` | toolbar_entries | **HIGH** | `toolbar_element.element_kind` enum |
| `ShapeItem` / `ShapeDefinition` | items, shapes | **HIGH** | `dump_source_type`; domain is `shape_recipe` |
| `UnityEngine.Object` | prefabs, sprites, materials, many envelopes | **MEDIUM** | `dump_source_type` column |
| `asset.meta` / `UnityEngine.Object` (meta) | asset_references | **MEDIUM** | `dump_source_type` on meta row |
| `IPresentableToolbarElementData.Icon` | toolbar_entries | **HIGH** if column name used | Extract `icon_sprite_name` only |
| `ISimulationSystem.OnSimulationCreated` | simulation_systems | **CRITICAL** | `simulation_runtime_audit` or drop |
| `<*k__BackingField>` | research_unlocks, building_groups, many | **HIGH** | Strip on import; `unknown_property` if needed |
| `$type` | all nested snapshots | **MEDIUM** | Map to enum tables; never table per `$type` |
| `$unity` + `instance_id` | items, shapes, toolbar, building_groups | **HIGH** | Never store `instance_id` as FK |
| `Core.Localization.LazyLocalizedText` | building_groups, toolbar | **MEDIUM** | Store resolved `message_key` only |
| `LazyLocalizedTextPlaceholderResolver` | building_groups | **MEDIUM** | l10n infrastructure, not domain entity |
| `Game.Content.*` assembly strings | raw_type_index | **MEDIUM** | `assembly_name` bucket only |
| `ResearchUnlockManager` | research_unlocks | **HIGH** | Singleton → `research_global_config` + layout index, not a entity table |
| `ToolbarSlotSeparator` as table name | toolbar_entries | **MEDIUM** | `toolbar_element.element_kind=separator` |
| `#166` / memory-style ids | not observed in exports | **LOW** | Reject if appear |

---

## Correct placement tier

| Tier | Store as |
| ---- | -------- |
| Domain tables | Game meaning only (variant, recipe, upgrade, …) |
| `unknown_property` | Unmapped keys |
| `simulation_runtime_audit` / `source_object_record` | Opaque captures |
| Import batch tables | Manifest + hashes + warnings |

---

## Reports with strongest leakage discipline

Best: **asset_references**, **prefabs**, **sprites**, **materials**, **fluids**, **manifest**  
Needs enforcement: **simulation_systems**, **toolbar_entries**, **research_unlocks**
