# Global Entity Registry

Cross-scan of **153** reports under `documents/game_data_analysis/**` (17 JSON stems × 9 files).

Normalization rule: names below are **canonical working names**; report-local aliases noted in *Origins*.

---

## Infrastructure & provenance

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `game_data_import_batch` | all 17 | Single export bundle identity | `manifest_self_hash` or `(dump_timestamp_utc, dump_schema_version, dump_mod_version)` | parent of all imports | **Approved** |
| `game_data_artifact_checksum` | manifest | Per-file SHA-256 gate | `(import_batch_id, artifact_filename)` | → batch | **Approved** |
| `export_warning` | manifest | Export caveats | `(import_batch_id, warning_index)` | → batch | **Approved** |
| `export_incomplete_section` | manifest, translations | Failed sections | `(import_batch_id, section_code)` | → batch | **Approved** |
| `localization_export_status` | translations | Empty/incomplete l10n | `import_batch_id` 1:1 | overlaps `export_incomplete_section` | **Needs review** |
| `source_object_record` | most (planned) | JSON row audit | `(import_batch_id, source_file, source_index)` | → batch | **Approved** |
| `unknown_property` | all (planned) | Unmapped JSON keys | `(parent_table, parent_id, property_key)` | audit | **Approved** |

---

## Asset content & meta bridge

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `prefab_asset` | prefabs, asset_references | Prefab content identity | `stable_id` / `prefab_path` | ← meta | **Approved** (merge candidate) |
| `sprite_asset` | sprites, asset_references | Icon/sprite content | `stable_id` / `sprite_path` | ← meta | **Approved** (merge candidate) |
| `material_asset` | materials, asset_references | Material content | `stable_id` / `material_path` | ← meta | **Approved** (merge candidate) |
| `asset_meta_reference` | asset_references | .meta → content bridge | `meta_stable_id` | → content by kind | **Approved** |

---

## Buildings & placement geometry

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `building` | buildings | Player-facing buildable **group** (plain display keys) | `group_key` (= `source_guid`) | → members, rules | **Approved** |
| `building_group` | building_groups | Same 67 families with LazyText overlay | `group_key` / `stable_id` | → members, l10n | **Needs review** (vs `building`) |
| `building_variant` | building_variants, buildings, building_groups, belts_pipes_transport | Internal variant geometry + connectors | `internal_name` (`Id.Name`) | connectors, tiles | **Approved** (canonical owner: **building_variants**) |
| `building_connector` | building_variants, building_groups, buildings, belts_pipes_transport | IO endpoints | `(building_variant_id, ordinal)` | → variant | **Approved** |
| `building_footprint_tile` | building_variants, belts_pipes_transport | Occupied tiles | `(building_variant_id, ordinal)` or coords | → variant | **Approved** |
| `building_variant_custom_config` | building_variants, belts_pipes_transport | Simulation/render extras | `(building_variant_id, config_kind, config_key)` | → variant | **Needs review** |
| `building_variant_legacy_io` | building_variants | Legacy IO graph | `(building_variant_id, slot_kind, ordinal)` | → variant | **Defer** |
| `building_group_member` | buildings, building_groups | Group → variant membership | `(parent_group_id, ordinal)` | → variant | **Approved** (unify parent FK) |
| `building_placement_rule` | buildings, building_groups | Placement constraints | `(building_id or building_group_id, ordinal)` | → group | **Needs review** |
| `building_simulation_setting` | buildings | Sim/UI flags per group | `building_id` 1:1 | → building | **Approved** |
| `building_group_simulation_setting` | building_groups | Same flags on group row | `building_group_id` 1:1 | → building_group | **Merge?** with `building_simulation_setting` |
| `building_localization_overlay` | building_groups, buildings | LazyText title/description | `group_key` | → building/group | **Approved** |
| `building_group_localization_ref` | building_groups | LazyText keys only | `building_group_id` | → group | **Merge?** into overlay |
| `transport_building_registry` | belts_pipes_transport | Transport-kind registry (9 kinds) | `transport_kind` | → variant snapshot | **Approved** (not duplicate of `building`) |

---

## Shapes & fluids

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `shape_recipe` | items, shapes, research_unlocks | Shape code / operation | `shape_hash`, `operation_uid` | layers, slots | **Approved** (single table; items⊂shapes) |
| `shape_recipe_layer` | items, shapes | Layer stack | `(shape_recipe_id, layer_index)` | → recipe | **Approved** |
| `shape_quadrant_slot` | items, shapes | Quadrant shape+color | `(layer_id, quadrant_index)` | → kinds, fluid | **Approved** |
| `shape_component_kind` | items, shapes | Subpart lookup | `component_key` | — | **Approved** |
| `fluid_color` | fluids, items, shapes | Paint/fluid palette (`fluid_kind` enum column) | `color_name` | ← slots | **Approved** |

---

## Research progression

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `research_upgrade` | research_unlocks | Upgrade id registry | `upgrade_key` | prereqs, quests | **Approved** |
| `research_milestone` | research_unlocks | Main ladder node | `node_key` | costs, rewards | **Approved** |
| `research_side_quest` | research_unlocks | Side quest | `node_key` | costs, rewards | **Approved** |
| `research_side_upgrade` | research_unlocks | Side upgrade | `node_key` | prereqs | **Approved** |
| `research_mechanic` | research_unlocks | Mechanic gate | `mechanic_key` | prereqs | **Approved** |
| `research_unlock_cost` | research_unlocks | Shape payment | `(parent_id, sort_order)` | → shape_recipe | **Approved** |
| `research_unlock_reward` | research_unlocks | Reward line | `(parent_id, sort_order)` | — | **Approved** |
| `research_prerequisite` | research_unlocks | Upgrade/mechanic deps | `(parent_id, required_key)` | → upgrade/mechanic | **Approved** |
| `research_global_config` | research_unlocks | Global tunables | `import_batch_id` singleton | — | **Approved** |
| `progression_layout_index` | research_unlocks (inferred) | Manager layout index | TBD | → nodes | **Needs review** |

---

## Simulation & toolbar

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `simulation_system_entry` | simulation_systems | CLR sim registration | `stable_id` + `simulation_kind_key` | factory/audit children | **Approved** |
| `simulation_factory_stub` | simulation_systems | Factory-only shell | `simulation_system_entry_id` | → entry | **Approved** |
| `global_belt_speed_policy` | simulation_systems | Belt speed buff | `import_batch_id` | → research_upgrade | **Approved** |
| `connectable_simulation_attachment` | simulation_systems | Connectable graph slot | `(entry_id, attachment_index)` | building audit | **Needs review** |
| `simulation_runtime_audit` | simulation_systems | Heavy CLR capture | `simulation_system_entry_id` | audit JSON only | **Approved** |
| `toolbar_element` | toolbar_entries | Flattened toolbar node | `tree_path` (= display_name_key) | tree edges | **Approved** |
| `toolbar_tree_edge` | toolbar_entries | Parent/child | `(parent_id, child_id, child_index)` | → elements | **Approved** |
| `toolbar_building_placement` | toolbar_entries | Places building variant | `toolbar_element_id` | `building_definition_key` | **Approved** |
| `toolbar_island_placement` | toolbar_entries | Island placement | `toolbar_element_id` | `island_group_name` | **Approved** |
| `toolbar_group_node` | toolbar_entries | Folder/category | `toolbar_element_id` | mechanic_key? | **Approved** |
| `toolbar_separator` | toolbar_entries | Separator | `toolbar_element_id` | — | **Approved** |

---

## Reflection catalog

| Entity | Origins | Purpose | Natural key | FK / refs | Review |
| ------ | ------- | ------- | ----------- | --------- | ------ |
| `clr_type_registry_entry` | raw_type_index | CLR type catalog | `(type_name, assembly_name)` | optional manifest DLL | **Approved** |
| `localized_message` | translations (planned) | Resolved strings | `(message_key, locale_code)` | all LazyText | **Approved** (0 rows today) |
| `localized_message_placeholder` | translations (planned) | Template slot replacements | `(message_id, slot_index)` | → message | **Needs review** |

---

## Rejected as domain entities (registry note)

| Dump label | Keep as |
| ---------- | ------- |
| `ShapeItem`, `ShapeDefinition`, `BuildingDefinition` | metadata / nested extract only |
| `AtomicStateful*System`2[[…]]` | `clr_type_audit` / `simulation_system_entry.clr_type_audit` |
| `UnityEngine.Object` | `dump_source_type` column |
| `Game.Core.Research.ResearchUpgradeId` | row discriminator only |

---

## Entity count summary

| Category | Tables |
| -------- | ------ |
| Infrastructure | 7 |
| Assets | 4 (+ 3 merge candidates) |
| Buildings | 12 |
| Shapes/fluids | 6 |
| Research | 9 |
| Simulation/toolbar | 10 |
| Reflection/l10n | 2 |
| **Total distinct canonical** | **~52** (post-merge target **~42**) |

**Report coverage:** 17 stems × 9 files = **153** markdown files scanned (`00`–`08` per stem + cross-audit).
