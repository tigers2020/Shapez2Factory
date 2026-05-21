# Reconstructed Schema — `items.json`

## Overview table

| Table | Purpose | Domain question answered | Source paths | Cross references | Review status |
| ----- | ------- | ------------------------ | ------------ | ---------------- | ------------- |
| `source_object_record` | Dump provenance | Which JSON row produced this row? | envelope | `import_run` | ready |
| `shape_component_kind` | Subpart lookup | What geometric subpart is this quadrant? | `Parts[].Shape.name` | — | ready |
| `shape_recipe` | Recipe header | What is this shape operation / hash code? | `Definition.*` | layers | ready |
| `shape_recipe_layer` | Layer stack | Which layer in a multi-layer shape? | `Layers[]` | recipe, slots | ready |
| `shape_quadrant_slot` | Quadrant fill | Shape+color at quadrant Q on layer L? | `Parts[]` | layer, kinds, color | ready |
| `unknown_property` | Extension capture | Unmapped JSON keys? | any | source_object_record | ready |

**Not proposed:** `items_raw_json`, `ShapeItem`, JSONField arrays for `Layers`/`Parts`.

---

## `shape_component_kind`

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | PK | — | | no | |
| `component_key` | Stable key | `Shape.name` | no | no | **UNIQUE** |
| `catalog_shape_code` | Planner letter | map from `shape_catalog.SHAPE_KINDS` | yes | yes | e.g. `C`→Circle |
| `display_label` | UI | derived | yes | yes | |

**Domain question:** What subpart kinds exist in the item catalog?

**Review:** Map `PinQuad`→`P`, `CircleQuad`→`C`, etc. against `SHAPE_KINDS`.

---

## `shape_recipe`

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | PK | surrogate | | no | |
| `operation_uid` | Game id | `UniqueOperationId`, `Id.Uid` | no | no | **UNIQUE** |
| `shape_hash` | Encoded code | `Hash` | no | no | **UNIQUE** |
| `quadrant_count` | Slots per layer | `PartCount` | no | no | CHECK = 4 |
| `layer_count` | Stack depth | `len(Layers)` or hash segments | yes | no | |
| `source_object_record_id` | Audit | envelope index | no | yes | FK |

**Domain question:** What distinct shape recipes exist for the planner?

**Indexes:** UNIQUE(`operation_uid`), UNIQUE(`shape_hash`).

**Human review:** Do not use envelope `stable_id` as PK.

---

## `shape_recipe_layer`

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | PK | — | | no | |
| `shape_recipe_id` | Parent | FK | no | no | FK |
| `layer_index` | Order | array index | no | no | |
| `hash_segment` | Layer token | split `Hash` on `:` | yes | yes | |
| `sort_order` | Display/sim order | `layer_index` | no | no | |

**Unique:** (`shape_recipe_id`, `layer_index`).

**Domain question:** How are layers ordered in a stacked shape?

---

## `shape_quadrant_slot`

| Column | Meaning | Source | Inferred? | Nullable | Constraints |
| ------ | ------- | ------ | --------- | -------- | ----------- |
| `id` | PK | — | | no | |
| `shape_recipe_layer_id` | Parent layer | FK | no | no | FK |
| `quadrant_index` | 0–3 | `Parts` index | no | no | CHECK 0–3 |
| `shape_component_kind_id` | Subpart | `Shape.name` | no | yes | FK; null if empty |
| `fluid_color_id` | Paint | `Color.name` | no | yes | FK; null if empty |
| `is_empty_shape` | No geometry | `Shape == ""` | no | no | default false |
| `is_empty_color` | No paint | `Color == ""` | no | no | default false |
| `hash_token` | Two-char code | inferred from `Hash` | yes | yes | review |

**Unique:** (`shape_recipe_layer_id`, `quadrant_index`).

**Domain question:** What shape and color occupy each quadrant?

**FK:** `fluid_color` imported from `fluids.json` first (match on `color_name`).

---

## `source_object_record` / `unknown_property`

Same pattern as other `game_data_analysis/*` reports: envelope + unmapped keys only.

---

## Entity diagram (logical)

```text
shape_recipe
  └─ has many → shape_recipe_layer (ordered)
        └─ has many → shape_quadrant_slot (4 per layer)
              ├─ FK → shape_component_kind
              └─ FK → fluid_color
```
