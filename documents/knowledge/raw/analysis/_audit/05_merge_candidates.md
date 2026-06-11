# Merge Opportunities

Requires similar purpose, attributes, lifecycle, and ownership — not name similarity alone.

| Candidate tables | Merge confidence | Recommendation |
| ---------------- | ---------------: | -------------- |
| `prefab_asset` + `sprite_asset` + `material_asset` | **92** | → **`game_content_asset`** with `content_kind` enum (`prefab`,`sprite`,`material`) and shared columns (`stable_id`, `content_path`, `display_name_key`, …) |
| `shape_recipe` / `shape_recipe_layer` / `shape_quadrant_slot` (items + shapes docs) | **98** | Already one model; enforce **single importer module** |
| `building` + `building_group` | **85** | → **`building_group`** canonical; ingest `buildings.json` as `display_profile=plain` or merge keys |
| `building_simulation_setting` + `building_group_simulation_setting` | **88** | → **`building_simulation_setting`** FK to unified group |
| `building_localization_overlay` + `building_group_localization_ref` | **83** | → **`building_localization_overlay`** |
| `building_group_member` (two reports) | **95** | → single **`building_group_member`** with FK to unified group |
| `building_variant` + belts_pipes_transport variant rows | **60** | **Do not merge tables** — same data, import once from `building_variants.json`; belts file is checksum-only duplicate |
| `export_incomplete_section` + `localization_export_status` | **65** | Keep separate; add FK/link `localization_export_status.incomplete_section_id` optional |
| `simulation_runtime_audit` + `unknown_property` | **40** | Keep separate — different retention policies |
| `source_object_record` (planned) + row-level `stable_id` | **55** | Keep `source_object_record` for index; do not duplicate as entity PK |
| `toolbar_group_node` + `toolbar_element` (group kind) | **50** | Keep separate kinds on `toolbar_element.element_kind` instead of merge |
| `research_milestone` + `research_side_quest` + `research_side_upgrade` | **45** | Keep separate node tables (different rules); share `research_unlock_cost` child |
| `connectable_simulation_attachment` + `building_connector` | **35** | **Do not merge** — different abstraction levels |

---

## Post-merge target schema size

~**42** domain tables (down from ~50), excluding audit-only tables.
