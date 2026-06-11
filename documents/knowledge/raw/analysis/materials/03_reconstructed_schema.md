# Reconstructed Schema — `materials.json`

**Principle:** Align with `asset_references` analysis — `material_asset` is the canonical content table. Four rows, four records. No `raw_json`.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `material_asset` | Material content registry | Which render materials exist in the bundle? | `[*]` | ← `asset_meta_reference` | Observed |
| `game_data_import_batch` | Provenance | Which dump? | `manifest.json` | → all | Observed |
| `source_object_record` | Row audit | Which JSON index? | `[i]` envelope | → batch | Planned |
| `unknown_property` | Extensions | New keys? | any | audit | Planned |

---

## `material_asset`

**Domain question:** “What material asset paths can meta references and render systems resolve?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `stable_id` | Content hash ID | `[*].stable_id` | observed | NO | **UNIQUE** |
| `material_path` | Resource path / name | `[*].material_path` | observed | NO | **UNIQUE** |
| `logical_path` | Unity asset path | `[*].source_path` | observed | NO | UNIQUE (duplicate of material_path in dump) |
| `display_name_key` | i18n key | `[*].display_name_key` | observed | NO | |
| `dump_source_type` | Exporter type label | `[*].source_type_name` | source metadata | NO | |
| `unity_source_guid` | Engine GUID | `[*].source_guid` | source metadata | YES | empty in dump |
| `import_batch_id` | FK | manifest | inferred | NO | FK |
| `source_row_index` | Array order | index `i` | inferred | NO | UNIQUE per batch |

**Indexes:** `UNIQUE(stable_id)`, `UNIQUE(material_path)`, `UNIQUE(import_batch_id, source_row_index)`.

**Human review:** Drop redundant `logical_path` if always equal to `material_path`; or keep for prefab/sprite symmetry.

**Do not use:** `source_type_name` as table or PK name.

---

## `asset_meta_reference` (sibling file — inbound FK)

Not populated from `materials.json`, but **must** resolve after materials import:

| Column | Links to |
| ------ | -------- |
| `content_stable_id` | `material_asset.stable_id` |
| `asset_kind` | `material` |

---

## Anti-patterns rejected

| Rejected | Why |
| -------- | --- |
| `materials_raw_json` | Forbidden |
| Model `UnityEngineObject` | Runtime label |
| JSONField storing 4-element array | Normalize to rows |
| Mirror `asset_references` into same table | Separate meta vs content |
