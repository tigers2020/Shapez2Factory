# JSON Path Mapping — `shapes.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ----- |
| `[i].stable_id` | Dump hash | source metadata | `shape_recipe` | `dump_stable_id` | unique in shapes |
| `[i].display_name_key` | Row label `#N` | source metadata | — | — | not domain |
| `[i].source_type_name` | `ShapeDefinition` | source metadata | — | — | |
| `[i].definition_snapshot` | Recipe body | domain entity | `shape_recipe` | — | no `.Definition.` |
| `…UniqueOperationId` | Operation id | entity attribute | `shape_recipe` | `operation_uid` | UNIQUE |
| `…Hash` | Shape code | entity attribute | `shape_recipe` | `shape_hash` | UNIQUE |
| `…PartCount` | Quadrants | entity attribute | `shape_recipe` | `quadrant_count` | =4 |
| `…Layers[]` | Layers | ordered child | `shape_recipe_layer` | — | |
| `…Layers[L].Parts[Q].Shape.name` | Subpart | enum | `shape_component_kind` | lookup | |
| `…Parts[Q].Color.name` | Color | enum | `fluid_color` | lookup | |
| `…Parts[Q].Shape.instance_id` | Runtime id | runtime metadata | — | — | |
| `Hash` split by `:` | Layer token | inferred | `shape_recipe_layer` | `hash_segment` | |
| `items.json` `Definition.Hash` | Same as shapes | relationship | same `shape_recipe` | | 70 subset |
| `research_unlocks` `ShapeHash` | Cost reference | relationship | `shape_recipe` | `shape_hash` | 253 refs |

**Importer note:** Map `items.json` paths by inserting virtual `Definition` segment or dual-path extractor.
