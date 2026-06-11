# Domain Classification — `raw_type_index.json`

## Per-element fields

| JSON path | Classification | Notes |
| --------- | -------------- | ----- |
| `[i]` | source metadata (row) | Reflection catalog entry — not a game entity instance |
| `[i].type_name` | entity attribute | Short CLR name; part of canonical key |
| `[i].assembly_name` | entity attribute | Assembly bucket; part of canonical key |
| `[i].stable_id` | source metadata | Hash; **not unique** |
| `[i].source_type_name` | runtime / reflection / debug metadata | Duplicate of `type_name` |
| `[i].source_path` | source metadata | Always empty |
| `[i].source_guid` | source metadata | Always empty |
| `[i].display_name_key` | source metadata | Always empty |

## Row-level domain role (inferred)

| Subset | Classification | Use |
| ------ | -------------- | --- |
| Content/simulation types (`Game.Content*`, `*Simulation*`) | unknown / needs human review | Lookup when resolving other dumps |
| Compiler-generated (`+<>`, `<PrivateImplementationDetails>`) | runtime / reflection / debug metadata | Filter from planner-facing joins |
| Unity source generated mono script types | runtime / reflection / debug metadata | Duplicate `stable_id` clusters |

## Rejected as domain entities

| Label | Reason |
| ----- | ------ |
| Table `ShapeOperationPaintPayload` | Single CLR type name |
| Table per `assembly_name` (37 tables) | Mirror dump structure |
| `stable_id` as UNIQUE PK | 114 collisions |

## Inferred registry entity

| Entity | Purpose |
| ------ | ------- |
| **CLR type registry entry** | Map (`type_name`, `assembly_name`) → audit hash; optional flags |

## Enum / choice

| Set | Values |
| --- | ------ |
| `assembly_name` | 37 observed assemblies |
| `is_compiler_generated` | inferred boolean rule on `type_name` pattern |
