# JSON Path Mapping — `fluids.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[*]` | Palette row | domain entity | `fluid_color` | (row) | — | 9 rows |
| `[*].definition_snapshot.Color.name` | Color label | domain entity key | `fluid_color` | `color_name` | unique | **Canonical** |
| `[*].definition_snapshot.Color.$unity` | Engine type | source metadata | `fluid_color` | `unity_color_type` | | `MetaShapeColor` |
| `[*].definition_snapshot.Color.instance_id` | Unity object id | runtime metadata | `fluid_color` | `unity_instance_id` | audit | Do not FK |
| `[*].definition_snapshot.$type` | Serializer type | runtime metadata | `fluid_kind` enum | `fluid_kind` | | `ColorFluid` |
| `[*].stable_id` | Dump hash (repeated) | source metadata | `fluid_color` | `dump_stable_id` | non-unique | Same all rows |
| `[*].source_guid` | Dump object label | source metadata | — | — | | constant |
| `[*].display_name_key` | Display key | source metadata | — | — | | constant `ColorFluid` |
| `[*].source_type_name` | Capture type | source metadata | import audit | — | | |
| `[*].source_path` | Empty | source metadata | — | — | | |
| `[].$index` | Palette order | ordered child | `fluid_color` | `source_row_index` | unique per batch | 0=Red … 8=Uncolored |

## Inferred mappings (domain code, not in JSON)

| Source | Target table | Target column |
| ------ | ------------ | ------------- |
| `COLOR_KINDS` in `shape_catalog.py` | `fluid_color` | `solver_color_code` |
| `FLUID_SOURCE_PRIMARY_COLORS` | `fluid_color` | `is_primary_source` |

## Sibling consumer paths (not in fluids.json)

| Consumer path | Links via |
| ------------- | --------- |
| `items.json[*].definition_snapshot…Color.name` | `fluid_color.color_name` |
| `shapes.json` (textual) | name validation |
| Shape codes in planner | `solver_color_code` |
