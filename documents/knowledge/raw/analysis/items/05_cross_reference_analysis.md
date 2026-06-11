# Cross-Reference Analysis — `items.json`

## Relationship diagram

```text
source_object_record
  └─ documents → shape_recipe (1:1 by source_index)

shape_recipe
  └─ has many → shape_recipe_layer (ordered by layer_index)
        └─ has many → shape_quadrant_slot (4 per layer, quadrant_index 0–3)
              ├─ FK → shape_component_kind (by component_key)
              └─ FK → fluid_color (by color_name)

shape_component_kind
  └─ maps to → shape_catalog.SHAPE_KINDS (application layer, not DB dump)

fluid_color
  └─ imported from → fluids.json (prerequisite)
```

## FK relationships (proposed)

| From | To | Cardinality | Resolution key |
| ---- | -- | ----------- | -------------- |
| `shape_recipe_layer` | `shape_recipe` | N:1 | `shape_recipe_id` |
| `shape_quadrant_slot` | `shape_recipe_layer` | N:1 | `shape_recipe_layer_id` |
| `shape_quadrant_slot` | `shape_component_kind` | N:1 | `Shape.name` → `component_key` |
| `shape_quadrant_slot` | `fluid_color` | N:1 | `Color.name` → `color_name` |
| `shape_recipe` | `source_object_record` | N:1 | optional audit |

## M2M

None in this file. Recipes are self-contained trees.

## Ordered children

| Parent | Child | Order key |
| ------ | ----- | --------- |
| `shape_recipe` | `shape_recipe_layer` | `layer_index` |
| `shape_recipe_layer` | `shape_quadrant_slot` | `quadrant_index` |

## Inferred references by ID

| Reference | Target | Status |
| --------- | ------ | ------ |
| `operation_uid` | internal recipe identity | **resolved** (70 unique) |
| `shape_hash` | planner/solver shape string | **resolved** (70 unique) |
| `Color.name` | `fluid_color` | **resolved** if fluids imported |
| `Shape.name` | `shape_component_kind` | **resolved** (8 values) |

## Unresolved / external references

| Reference | Issue |
| --------- | ----- |
| `shapes.json` (1170 entries) | Overlap with `Hash` not fully catalogued — may be superset or different export |
| `building_variants` / asteroid `T` field | Layout uses variant strings, not necessarily `items.Hash` |
| `display_name_key` | No translation row linked |

## Source metadata references

| Field | Use |
| ----- | --- |
| `stable_id` | Audit correlation only (duplicate across rows) |
| `$type`, `$unity` | Import run diagnostics |

## Unknown references needing review

| Item | Risk |
| ---- | ---- |
| Hash letter `k` (Black) | Not in `COLOR_KINDS` — extend enum or separate mapping table |
| Empty JSON layer vs hash `--------` | Consistency rule for validation |
| `ConverterQuad_LV0` / `LV1` | Tier linkage to buildings? |

## Anti-patterns avoided

- No FK on `stable_id` (non-unique)
- No FK on `instance_id`
- No single JSON blob for `Layers`/`Parts`
