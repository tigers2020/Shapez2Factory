# JSON Path Mapping — `toolbar_entries.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ----- |
| `[i].stable_id` | Row hash | source metadata | `toolbar_element` | `stable_id` | UNIQUE |
| `[i].display_name_key` | Tree path | entity attribute | `toolbar_element` | `tree_path` | UNIQUE |
| `[i].source_type_name` | Kind | enum | `toolbar_element` | `element_kind` | mapped enum |
| `[i].definition_snapshot.Children[]` | Nested kids | ordered child | `toolbar_tree_edge` | `child_index` | also flat rows |
| `…BuildingDefinition.Id.Id` | Variant key | entity attribute | `toolbar_building_placement` | `building_definition_key` | |
| `…BuildingDefinition.IsTransportBuilding` | Flag | entity attribute | `toolbar_building_placement` | `is_transport_building` | |
| `…Icon.name` | Sprite | relationship | `toolbar_building_placement` | `icon_sprite_name` | → sprites |
| `…IslandGroup.Id.Name` | Group | entity attribute | `toolbar_island_placement` | `island_group_name` | |
| `…MechanicRequiredToUnlock.Id` | Gate | relationship | `toolbar_group_node` | `mechanic_key` | → research |
| `…PlacerId.Id` | Placer | entity attribute | placement tables | `placer_id` | |
| `IPresentableToolbarElementData.*` | Interface | runtime metadata | — | — | skip |
| `$type`, `$unity`, `instance_id` | Runtime | runtime metadata | audit | — | |
