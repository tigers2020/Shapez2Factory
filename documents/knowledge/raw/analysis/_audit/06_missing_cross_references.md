# Missing Cross References

Links that should exist for a coherent planner DB but are absent or only textual in dumps.

| Source | Missing target | Evidence | Confidence |
| ------ | -------------- | -------- | ---------: |
| `toolbar_building_placement` | `building_variant` | `BuildingDefinition.Id.Id` matches `internal_name`; no UUID | **92** |
| `toolbar_building_placement` | `sprite_asset` / `game_content_asset` | `icon_sprite_name` e.g. `BeltIcon` | **88** |
| `research_upgrade` | `building_group` / `building_variant` | `SG_*` / `Milestone_*` keys; textual in building_groups | **75** |
| `research_unlock_reward` | `building_variant` / `research_upgrade` | Reward `$type` variants not fully enum-mapped | **70** |
| `simulation_system_entry` | `building_variant` | Name overlap only; no stable_id | **65** |
| `connectable_simulation_attachment` | `building_variant` | Nested `Building.Definition` blob | **80** |
| `building_group_member` | `building_variant` | FK planned but `building_group_id` empty in variant dump | **85** (import order) |
| `building_variant` | `building_group` | `building_group_id` column nullable, not in JSON | **90** |
| `asset_meta_reference` | `game_content_asset` | Designed FK; must import content before meta | **95** |
| `localized_message` | all LazyText keys | translations.json empty | **95** |
| `shape_recipe` | `shape_component_kind` | Letter code mapping in shape_catalog.py not in DB | **60** |
| `transport_building_registry` | `simulation_system_entry` | transport_kind in simulation text | **55** |
| `research_prerequisite` | `research_milestone` polymorphic parent | Separate tables per node kind — need `research_node` supertype or `parent_kind` | **70** |
| `toolbar_element` | `research_mechanic` | `MechanicRequiredToUnlock` on categories | **78** |
| `global_belt_speed_policy` | `research_upgrade` | Documented; needs FK constraint test | **90** |
| `building_placement_rule` | `building_footprint_tile` | Rules vs geometry — semantic related | **50** |
| `clr_type_registry_entry` | dumps `source_type_name` | Optional validation only | **55** |
| `prefab_asset` | `building_variant` | Prefabs are visual LOD meshes, weak name overlap | **45** |

---

## Recommended FK additions (implementation phase)

1. `toolbar_building_placement.building_variant_id` → `building_variant.id` (resolve via `building_definition_key`).
2. `research_unlock_cost.shape_recipe_id` → `shape_recipe.id` (resolve via `shape_hash`).
3. `asset_meta_reference` polymorphic validator → `game_content_asset`.
4. `building_group_member.building_variant_id` → `building_variant.id` (required after both imports).
5. `building_group_member.building_group_id` → `building_group.id`.
