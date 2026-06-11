# JSON Path Mapping — `raw_type_index.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Relationship | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ------------ | ----- |
| `[i]` | Type index row | source metadata | `clr_type_registry_entry` | — | — | `source_row_index=i` |
| `[i].type_name` | CLR short name | entity attribute | `clr_type_registry_entry` | `type_name` | — | composite UK |
| `[i].assembly_name` | Assembly bucket | entity attribute | `clr_type_registry_entry` | `assembly_name` | — | composite UK |
| `[i].stable_id` | Dump hash | source metadata | `clr_type_registry_entry` | `dump_stable_id` | — | not unique |
| `[i].source_type_name` | Redundant CLR label | runtime metadata | (drop or audit col) | — | — | equals type_name |
| `[i].source_path` | Unused path | source metadata | — | — | — | always "" |
| `[i].source_guid` | Unused GUID | source metadata | — | — | — | always "" |
| `[i].display_name_key` | Unused i18n | source metadata | — | — | — | always "" |
| `(inferred)` | Compiler-generated | runtime metadata | `clr_type_registry_entry` | `is_compiler_generated` | — | regex |
| `manifest.assembly_hashes` | DLL SHA-256 | source metadata | `assembly_catalog` | — | FK name match | external |
| `items.json[*].source_type_name` | e.g. `ShapeItem` | relationship | lookup join | `type_name` | optional FK | 1+ assemblies? |
| `manifest.file_hashes.raw_type_index.json` | File digest | source metadata | artifact checksum | — | — | |

## Canonical key mapping

| Business key | Columns |
| ------------ | ------- |
| Type identity | `type_name` + `assembly_name` |
| Audit hash | `dump_stable_id` (non-unique) |
