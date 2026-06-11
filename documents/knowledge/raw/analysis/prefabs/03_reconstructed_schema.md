# Reconstructed Schema — `prefabs.json`

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `prefab_asset` | Prefab content registry | Which prefab paths exist for meta/render links? | `[*]` | ← `asset_meta_reference` | Observed |
| `game_data_import_batch` | Provenance | Which dump? | `manifest.json` | → all | Observed |
| `source_object_record` | Row audit | Source index? | `[i]` | batch | Planned |
| `unknown_property` | Extensions | New keys? | any | audit | Planned |

---

## `prefab_asset`

**Domain question:** “What prefab content identities can the asset meta registry and render pipeline resolve?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `stable_id` | Content hash | `[*].stable_id` | observed | NO | **UNIQUE** |
| `prefab_path` | Resource path | `[*].prefab_path` | observed | NO | **UNIQUE** |
| `logical_path` | Unity path | `[*].source_path` | observed | NO | UNIQUE in practice |
| `display_name_key` | i18n key | `[*].display_name_key` | observed | NO | |
| `path_family` | Prefix family | parsed from `prefab_path` | inferred | YES | e.g. Wire, Pipe |
| `is_lod_variant` | LOD mesh row | `'LOD' in path` | inferred | NO | bool |
| `is_baked_mesh` | Baked representation | path pattern | inferred | NO | bool |
| `dump_source_type` | Exporter label | `[*].source_type_name` | source metadata | NO | |
| `unity_source_guid` | Engine GUID | `[*].source_guid` | source metadata | YES | always empty |
| `import_batch_id` | FK | manifest | inferred | NO | FK |
| `source_row_index` | Array index | `i` | inferred | NO | UNIQUE per batch |

**Indexes:** `UNIQUE(stable_id)`, `UNIQUE(prefab_path)`, `(path_family)`, `(import_batch_id, source_row_index)`.

**Human review:** `path_family` parser rules; whether LOD rows should link to parent building variant.

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `prefabs_raw_json` | Forbidden |
| Table per `prefab_path` | 764 mirror tables |
| `UnityEngineObject` model | Runtime label |
