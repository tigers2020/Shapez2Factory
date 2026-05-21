# JSON Path Mapping — `items.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[i]` | Recipe row | source metadata | `source_object_record` | `source_index` | — | i = 0..69 |
| `[i].stable_id` | Dump hash | source metadata | `source_object_record` | `stable_id` | — | **Not unique** |
| `[i].source_guid` | Type id | source metadata | `source_object_record` | `source_guid` | — | constant |
| `[i].source_type_name` | CLR type | source metadata | `source_object_record` | `source_type_name` | — | |
| `[i].display_name_key` | Key | source metadata | `source_object_record` | `display_name_key` | — | |
| `[i].source_path` | Asset path | source metadata | `source_object_record` | `source_path` | — | empty |
| `[i].definition_snapshot` | Wrapper | source metadata | — | — | — | not stored as JSON |
| `[i].definition_snapshot.Definition` | Recipe body | domain entity | `shape_recipe` | — | 1:1 | |
| `...Definition.UniqueOperationId` | Operation id | entity attribute | `shape_recipe` | `operation_uid` | — | UNIQUE |
| `...Definition.PartCount` | Quadrant count | entity attribute | `shape_recipe` | `quadrant_count` | — | always 4 |
| `...Definition.Hash` | Shape code | entity attribute | `shape_recipe` | `shape_hash` | — | UNIQUE |
| `...Definition.Id.Uid` | Id duplicate | entity attribute | `shape_recipe` | `operation_uid` | — | same as above |
| `...Definition.$type` | Serializer type | source metadata | — | — | — | audit optional |
| `...Definition.Layers[]` | Layer stack | ordered child | `shape_recipe_layer` | — | parent FK | |
| `...Layers[L]` | Layer L | ordered child | `shape_recipe_layer` | `layer_index` | FK recipe | L = 0..n-1 |
| `...Layers[L].Parts[]` | Quadrants | ordered child | `shape_quadrant_slot` | — | FK layer | len 4 |
| `...Parts[Q].Shape` | Subpart ref | relationship | `shape_quadrant_slot` | `shape_component_kind_id` | FK | `""` → empty |
| `...Parts[Q].Shape.name` | Kind name | enum / choice | `shape_component_kind` | `component_key` | lookup | |
| `...Parts[Q].Shape.$unity` | Unity type | source metadata | — | — | — | |
| `...Parts[Q].Shape.instance_id` | Runtime id | runtime metadata | — | — | — | never FK |
| `...Parts[Q].Color` | Color ref | relationship | `shape_quadrant_slot` | `fluid_color_id` | FK | `""` → empty |
| `...Parts[Q].Color.name` | Palette name | enum / choice | `fluid_color` | `color_name` | lookup | from fluids import |
| `...Parts[Q].Color.instance_id` | Runtime id | runtime metadata | — | — | — | |
| `Definition.Hash` (split `:`) | Per-layer token | entity attribute | `shape_recipe_layer` | `hash_segment` | inferred | index aligns with L |
| (unmapped keys) | — | unknown | `unknown_property` | `json_path`, `raw_value` | FK source | |

## Hash token derivation (inferred path)

| JSON path | Target | Notes |
| --------- | ------ | ----- |
| `Hash` segment at index L, chars `2*Q..2*Q+2` | `shape_quadrant_slot.hash_token` | **Inferred** — validate against Shape+Color |

---

## Import order dependency

1. `fluid_color` (from `fluids.json`)
2. `shape_component_kind` (distinct names from all `Parts[].Shape.name`)
3. `shape_recipe` → layers → slots
