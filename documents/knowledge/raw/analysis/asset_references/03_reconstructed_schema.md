# Reconstructed Relational Schema — `asset_references.json`

Design goal: normalize **meta-side asset identity** and its link to **canonical content assets** already modeled from sibling dumps. No `raw_json` primary tables. No tables named after `asset.meta` or `UnityEngine.Object`.

---

## Schema overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `prefab_asset` | Canonical prefab content | What prefab asset exists at path X? | `../prefabs.json` `[*]` | ← `asset_meta_reference` (prefab) | Observed |
| `sprite_asset` | Canonical sprite content | What sprite/icon asset exists? | `../sprites.json` `[*]` | ← `asset_meta_reference` (sprite) | Observed |
| `material_asset` | Canonical material content | What material asset exists? | `../materials.json` `[*]` | ← `asset_meta_reference` (material) | Observed |
| `asset_meta_reference` | Meta registry bridge | Which `.meta` stable identity maps to which content asset? | `asset_references.json` `[*]` | → prefab/sprite/material by `ref_stable_id` | Observed |
| `game_data_import_batch` | Dump provenance | Which export produced these rows? | `../manifest.json` | → all game_data tables | Observed (external) |
| `unknown_property` | Extension capture | What unrecognized keys appeared? | any future extra keys | → parent row | Planned |

---

## Table: `asset_meta_reference`

**Purpose:** Persist one row per `asset_references.json` element — the meta-file registry entry.

**Domain question:** “Given a meta `stable_id` (or asset path), which canonical prefab/sprite/material does the game data bundle associate with it?”

### Columns

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | BIGSERIAL |
| `meta_stable_id` | Meta-side hash ID | `[*].stable_id` | observed | NO | UNIQUE |
| `content_stable_id` | Target content asset | `[*].ref_stable_id` | observed | NO | INDEX |
| `asset_kind` | prefab / sprite / material | `[*].asset_type` | observed | NO | CHECK enum |
| `logical_path` | Unity asset path string | `[*].source_path` | observed | NO | UNIQUE |
| `display_name_key` | Localization lookup key | `[*].display_name_key` | observed | NO | |
| `source_label` | Exporter “guid” column | `[*].source_guid` | observed | YES | **Review rename** |
| `dump_source_type` | Capture channel | `[*].source_type_name` | observed | NO | default `asset.meta` |
| `import_batch_id` | FK to import batch | manifest | inferred | NO | FK |
| `source_row_index` | 0-based array index | array position | inferred | NO | UNIQUE per batch |
| `content_checksum` | Deterministic row hash | derived | inferred | NO | |

### Foreign keys

| FK column | References | On delete |
| --------- | ---------- | --------- |
| `content_stable_id` + `asset_kind` | Polymorphic: `prefab_asset.meta_stable_id` OR `sprite_asset` OR `material_asset` | RESTRICT |
| `import_batch_id` | `game_data_import_batch.id` | CASCADE |

**Polymorphic FK implementation options (review):**

1. **Recommended:** single `content_stable_id` + `asset_kind` with DB constraint enforced in import validator (no orphan).
2. Alternative: nullable `prefab_id`, `sprite_id`, `material_id` with CHECK exactly one set.

### Indexes

- `UNIQUE (meta_stable_id)`
- `UNIQUE (logical_path)`
- `UNIQUE (import_batch_id, source_row_index)`
- `(content_stable_id, asset_kind)`

### Human review notes

- Do not expose `meta_stable_id` to UI unless meta/content duality is required.
- `source_label` likely redundant with `logical_path` in current dump — consider dropping after confirming with dump pipeline.

---

## Table: `prefab_asset` (sibling file — FK target)

**Domain question:** “What is the canonical prefab content record for simulation/rendering references?”

| Column | Meaning | Source (`prefabs.json`) | Inferred? |
| ------ | ------- | ----------------------- | --------- |
| `id` | Surrogate PK | — | yes |
| `stable_id` | Content hash ID | `[*].stable_id` | observed |
| `logical_path` | Asset path | `[*].source_path` | observed |
| `display_name_key` | i18n key | `[*].display_name_key` | observed |
| `prefab_path` | Resource path | `[*].prefab_path` | observed |
| `dump_source_type` | `UnityEngine.Object` | `[*].source_type_name` | source metadata |
| `unity_source_guid` | Often empty | `[*].source_guid` | source metadata |

**Unique:** `stable_id`, `logical_path`

---

## Table: `sprite_asset` (sibling file — FK target)

Same pattern as prefab; `sprite_path` instead of `prefab_path`. 61 rows.

---

## Table: `material_asset` (sibling file — FK target)

Same pattern; `material_path`. 4 rows.

---

## Table: `game_data_import_batch`

| Column | Meaning | Source |
| ------ | ------- | ------ |
| `id` | PK | inferred |
| `game_version` | Game build label | `manifest.json` |
| `dump_schema_version` | Schema version | `manifest.json` |
| `dump_timestamp_utc` | Export time | `manifest.json` |
| `source_method` | e.g. `runtime_reflection` | `manifest.json` |
| `file_hash` | SHA-256 of `asset_references.json` | `manifest.file_hashes` |

**JSONField policy:** Only `unknown_property.raw_value` (audit) — not on domain tables.

---

## Table: `unknown_property`

| Column | Meaning |
| ------ | ------- |
| `id` | PK |
| `parent_table` | e.g. `asset_meta_reference` |
| `parent_id` | FK to parent surrogate |
| `property_key` | Unexpected JSON key |
| `raw_value` | JSON snapshot of value |
| `import_batch_id` | FK |

---

## Anti-patterns rejected

| Rejected approach | Why |
| ----------------- | --- |
| `asset_references_raw` with JSON blob | Violates no-dump-table rule |
| Table `asset_meta` mirroring JSON filename | Not domain language |
| Using `source_type_name` as model name | Source metadata only |
| Storing 829 rows as JSON array column | Arrays not in JSONField for domain data |
