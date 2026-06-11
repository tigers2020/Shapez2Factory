# Reconstructed Relational Schema — `fluids.json`

**Principle:** Nine rows = nine **`fluid_color`** palette entries. One **`fluid_kind`** constant. Do not use duplicate `stable_id` as unique key.

---

## Overview

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `fluid_color` | Paint/fluid palette | What discrete colors can shape fluid/paint take? | `[*].definition_snapshot.Color.name` | ← items/shapes (by name) | Observed |
| `fluid_kind` (enum / lookup) | Serializer family | What fluid type bucket applies? | `[*].$type` / `source_type_name` | constant | Observed |
| `game_data_import_batch` | Provenance | Which dump? | manifest | → all | Observed |
| `unknown_property` | Extensions | New keys | any | audit | Planned |

No separate table per `$type` string.

---

## Table: `fluid_color`

**Domain question:** “Which named colors exist in the color-fluid palette for shapes/items?”

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | Surrogate PK | — | yes | NO | PK |
| `color_name` | Canonical name | `Color.name` | observed | NO | UNIQUE |
| `fluid_kind` | Enum | constant `ColorFluid` | inferred | NO | CHECK |
| `solver_color_code` | Single-letter planner code | map to `COLOR_KINDS` | inferred | YES | UNIQUE? |
| `is_primary_source` | Primary vs mixed | domain rules | inferred | NO | bool |
| `dump_stable_id` | Non-unique hash | `[*].stable_id` | observed | NO | **not unique** |
| `unity_instance_id` | Runtime ref | `Color.instance_id` | observed | YES | audit |
| `unity_color_type` | Engine label | `Color.$unity` | source metadata | YES | |
| `source_row_index` | Array order | index | inferred | NO | UNIQUE |
| `import_batch_id` | FK | manifest | inferred | NO | FK |

**Unique constraints:** `UNIQUE(color_name)`, `UNIQUE(source_row_index)` per batch.

**Do not use:** `stable_id` as UNIQUE.

**Human review:** Add `slug` (`red`, `green`) denormalized from `solver_color_code` for stable APIs.

---

## Enum: `fluid_kind`

| Value | Source |
| ----- | ------ |
| `color_paint` | mapped from `$type: ColorFluid` |

(Only one value in this file; extend when dump adds other fluid types.)

---

## Optional: `fluid_color_solver_mapping`

Only if letter codes need DB-driven config instead of `shape_catalog.py`:

| Column | Notes |
| ------ | ----- |
| `fluid_color_id` | FK |
| `solver_code` | `r`, `g`, … |

Default: keep mapping in domain code; import only validates names exist.

---

## Anti-patterns rejected

| Rejected | Reason |
| -------- | ------ |
| `fluids_raw` JSON table | Forbidden |
| 9 rows with same PK `stable_id` | Data bug |
| Model `ColorFluid` | Dump `$type` name |
| Model `MetaShapeColor` | Unity type string |
| JSONField for palette | Use scalar columns |
