# Reconstructed Schema — `sprites.json`

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `sprite_asset` | Icon/sprite registry | Which sprite paths exist for UI/meta links? | `[*]` | ← `asset_meta_reference` | Observed |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `source_object_record` | Row audit | JSON index | `[i]` | batch | Planned |
| `unknown_property` | Extensions | New keys | any | audit | Planned |

---

## `sprite_asset`

**Domain question:** “What icon/sprite content identities can the meta registry resolve?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | PK | surrogate | yes | NO | PK |
| `stable_id` | Content hash | `[*].stable_id` | observed | NO | **UNIQUE** |
| `sprite_path` | Resource name | `[*].sprite_path` | observed | NO | **UNIQUE** |
| `logical_path` | Unity path | `[*].source_path` | observed | NO | = sprite_path |
| `display_name_key` | i18n key | `[*].display_name_key` | observed | NO | |
| `icon_family` | Prefix family | parse path | inferred | YES | e.g. LogicGate |
| `dump_source_type` | Exporter label | `[*].source_type_name` | source metadata | NO | |
| `unity_source_guid` | Engine GUID | `[*].source_guid` | source metadata | YES | empty |
| `import_batch_id` | FK | manifest | inferred | NO | FK |
| `source_row_index` | Order | `i` | inferred | NO | UNIQUE/batch |

**Do not use:** `UnityEngine.Object` as model name.

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `sprites_raw_json` | Forbidden |
| JSONField array of 61 icons | Normalize to rows |
