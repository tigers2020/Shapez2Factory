# Cross-Reference Analysis — `toolbar_entries.json`

```text
game_data_import_batch
  └─ has many → toolbar_element (204)
        ├─ 1:1 → toolbar_building_placement (78)
        ├─ 1:1 → toolbar_island_placement (63)
        ├─ 1:1 → toolbar_group_node / separator (54)
        └─ tree via → toolbar_tree_edge

toolbar_building_placement
  ├─ building_definition_key → building_groups / building_variants (textual Id)
  └─ icon_sprite_name → sprite_asset.sprite_path

toolbar_group_node
  └─ mechanic_key → research_mechanic (RUFluids, RUWires, …)

RootToolbarElementData (1 row)
  └─ Children[] → 9 top-level toolbar_element nodes
```

## FK status

| Link | Status |
| ---- | ------ |
| `building_definition_key` | **inferred** name match to `building_groups` |
| `icon_sprite_name` | **resolved** to `sprites.json` (61 icons) |
| `mechanic_key` | **resolved** to research mechanics |
| `asset_references` | **no** stable_id FK |

## Unresolved

- LazyLocalizedText → `translations.json` (empty)
- Full `BuildingDefinition` policy fields not all modeled

## Source metadata

- Interface-prefixed snapshot keys
- `simulation_parameters` per row (review overlap with buildings)
