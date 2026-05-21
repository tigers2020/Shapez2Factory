# Duplicate Entity Detection

Semantic comparison across reports. Similarity 0–100.

| Entity A | Entity B | Similarity | Merge recommendation | Reason |
| -------- | -------- | ---------: | -------------------- | ------ |
| `shape_recipe` (items) | `shape_recipe` (shapes) | **98** | **Merge** — single table; dual JSON path extractor | Same columns; shapes is superset (1170⊃70); items uses nested `Definition` wrapper |
| `shape_recipe_layer` | `shape_recipe_layer` (shapes/items) | **98** | Merge with above | Identical child model |
| `shape_quadrant_slot` | `shape_quadrant_slot` (shapes/items) | **98** | Merge with above | Same |
| `prefab_asset` | `sprite_asset` | **88** | **Merge** → `game_content_asset` + `content_kind` | Same envelope: stable_id, path, display_name_key, UnityEngine.Object |
| `sprite_asset` | `material_asset` | **88** | **Merge** → `game_content_asset` | Same pattern; only path column name differs |
| `prefab_asset` | `material_asset` | **85** | **Merge** → `game_content_asset` | Same |
| `building` (buildings) | `building_group` (building_groups) | **82** | **Unify** under `building_group` + optional `building_display_profile` | Same 67 `source_guid` families; buildings=plain keys, groups=LazyText; duplicate stable_id per file |
| `building_simulation_setting` | `building_group_simulation_setting` | **90** | **Merge** → `building_simulation_setting` on unified group | Same simulation_parameters fields |
| `building_localization_overlay` | `building_group_localization_ref` | **85** | **Merge** | Both store LazyText keys for same groups |
| `building_group_member` (buildings) | `building_group_member` (building_groups) | **92** | **Merge** — one table; FK to unified group | Same Definitions[] semantics |
| `building_variant` (building_variants) | `building_variant` (belts_pipes_transport snapshot) | **75** | **Keep separate import** — transport file is byte-equal snapshot, not second owner | Same schema path; single canonical import from building_variants |
| `export_incomplete_section` | `localization_export_status` | **72** | **Relate** — keep both; l10n status is specialization | translations section ⊆ incomplete_sections |
| `game_data_import_batch` | `game_data_import_batch` (all reports) | **100** | Already unified | Identical purpose every report |
| `unknown_property` | `unknown_property` (all) | **100** | Already unified | — |
| `source_object_record` | per-file audit rows | **70** | Optional merge into generic `source_row_audit` | Same shape, different source_file |
| `ResearchNode` (diagram examples) | `research_milestone` | **55** | **Keep separate** | Example diagrams only; no ResearchNode table proposed |
| `building` | `building_variant` | **45** | **Keep separate** | Group vs internal geometry — different lifecycle |
| `transport_building_registry` | `building_variant` | **50** | **Keep separate** | Kind-level registry vs full variant |
| `simulation_system_entry` | `building_variant_custom_config` | **40** | **Keep separate** | System registration vs per-variant config |
| `toolbar_building_placement` | `building` | **48** | **Keep separate** | UI placement row vs group definition |
| `asset_meta_reference` | `prefab_asset` | **35** | **Keep separate** | Meta vs content layer |
| `clr_type_registry_entry` | `shape_component_kind` | **25** | **Keep separate** | CLR catalog vs game subpart enum |

---

## High-confidence merges (action list)

1. **`game_content_asset`** replaces `prefab_asset`, `sprite_asset`, `material_asset` (add `content_kind` enum).
2. **`shape_recipe` family** — one importer, two JSON path profiles (`items` vs `shapes`).
3. **`building_group`** as canonical group table; deprecate parallel `building` table or map 1:1 with `profile=plain|lazy`.
4. **`building_simulation_setting`** — single table keyed by unified group id.
5. **`building_group_member`** — single membership table.
