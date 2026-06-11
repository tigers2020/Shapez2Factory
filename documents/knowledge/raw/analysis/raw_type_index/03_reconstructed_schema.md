# Reconstructed Schema — `raw_type_index.json`

**Principle:** Reflection catalog for import-time lookup and audit — **not** gameplay state. Do not name tables after CLR types.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `clr_type_registry_entry` | CLR type catalog | Which assembly defines CLR type T at dump time? | `[*]` | manifest assemblies; other dumps | Observed |
| `game_data_import_batch` | Provenance | Which dump? | `manifest.json` | → all | Observed |
| `source_object_record` | Row audit | JSON index? | `[i]` | batch | Planned |
| `unknown_property` | Extensions | New keys? | any | audit | Planned |

---

## `clr_type_registry_entry`

**Domain question:** “Given a `source_type_name` string from another JSON dump, which assembly was it loaded from in this export?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `type_name` | Short CLR name | `[*].type_name` | observed | NO | |
| `assembly_name` | Assembly bucket | `[*].assembly_name` | observed | NO | |
| `dump_stable_id` | Exporter hash | `[*].stable_id` | observed | YES | **not UNIQUE** |
| `source_type_name_redundant` | Copy of type_name | `[*].source_type_name` | observed | YES | drop column optional |
| `is_compiler_generated` | Closure/compiler type | pattern on `type_name` | inferred | NO | default false |
| `is_unity_generated` | Unity codegen type | name pattern | inferred | NO | default false |
| `import_batch_id` | FK | manifest | inferred | NO | FK |
| `source_row_index` | Array order | `i` | inferred | NO | UNIQUE per batch |

**Unique:** `(import_batch_id, type_name, assembly_name)` or global UNIQUE `(type_name, assembly_name)` per batch.

**Indexes:** `(type_name)`, `(assembly_name)`, `(type_name, assembly_name)` UNIQUE.

**Human review:** Whether planner queries need this table or only import-time validation.

**Do not use:** `stable_id` alone as UNIQUE; `type_name` alone as UNIQUE.

---

## Optional: `assembly_catalog` (from manifest, not this file)

Link `assembly_name` → `manifest.assembly_hashes` (`Game.Content.dll`). Populated from manifest import, not `raw_type_index.json`.

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `raw_type_index_raw_json` | Forbidden |
| 6497 tables named after `type_name` | C# mirror |
| Model `UnitySourceGeneratedAssemblyMonoScriptTypes_v1` | Runtime type |
| JSONField for 6497 array | Normalize to rows |
