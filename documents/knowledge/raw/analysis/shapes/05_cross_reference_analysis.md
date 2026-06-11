# Cross-Reference Analysis — `shapes.json`

## Diagram

```text
game_data_import_batch
  └─ has many → shape_recipe (1170)
        └─ has many → shape_recipe_layer
              └─ has many → shape_quadrant_slot
                    ├─ FK → shape_component_kind
                    └─ FK → fluid_color

shape_recipe
  ├─ superset of → items.json (70 hashes)
  └─ referenced by → research_unlock_cost.ShapeHash (253)

items.json
  └─ subset hashes → shape_recipe (identical geometry when matched)

fluids.json
  └─ palette → shape_quadrant_slot.fluid_color_id
```

## FK

| From | To | Key |
| ---- | -- | --- |
| layers / slots | `shape_recipe` | `shape_recipe_id` |
| slots | `fluid_color` | `Color.name` |
| slots | `shape_component_kind` | `Shape.name` |
| research costs | `shape_recipe` | `shape_hash` |

## Unresolved

- 1100 shapes not in `items.json` — gameplay relevance per shape
- Hash token grammar vs `shape_catalog.py` (`Ck` black, etc.)

## Source metadata

- `display_name_key` `#N`, `instance_id`, `$type`
