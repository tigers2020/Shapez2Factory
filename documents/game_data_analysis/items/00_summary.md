# File Inventory — `items.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/items.json` |
| File name | `items.json` |
| Manifest hash | `sha256:3d1e3a1aeaaa2c140fc14598ddf5850c76f9151bae06f17639c0789328d8b901` |
| Approx. size | **83,264 bytes** |
| Dump context | `manifest.json` → `source_method: runtime_reflection` |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **70** |
| Element type | **object** (homogeneous envelope + nested `Definition`) |
| Nesting depth | **~4** (`Definition` → `Layers[]` → `Parts[]` → `Shape`/`Color`) |

## Critical inventory finding

| Field | Distinct values | Notes |
| ----- | --------------- | ----- |
| `stable_id` | **1** | Same hash on all rows (dump reuse) |
| `source_guid` / `display_name_key` | **1** (`ShapeItem`) | Not per-recipe |
| `UniqueOperationId` | **70** | 946–1330 |
| `Id.Uid` | **70** | Matches `UniqueOperationId` |
| `Hash` | **70** | Shape-code string (planner-facing) |
| `PartCount` | **1** value: `4` | Quadrant model |

**Each array element = one distinct shape recipe** (multi-layer, 4 quadrants per layer).

## Major object groups

| Group | Count |
| ----- | ----- |
| Shape recipes (`ShapeItem`) | 70 |
| Layers per recipe | 1 (29), 2 (7), 3 (2), 4 (32) |
| Quadrant slots per layer | 4 (`Parts[]` length) |
| Total quadrant part records | **708** (70 recipes × varying layers) |

## Envelope fields (70/70)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `stable_id` | 64-char hex | **Non-unique** in dump |
| `source_guid` | string | `ShapeItem` |
| `source_type_name` | string | `ShapeItem` |
| `display_name_key` | string | `ShapeItem` |
| `source_path` | string | `""` |
| `definition_snapshot.Definition` | object | Core payload |

## `Definition` structure (repeated)

| Path | Type | Notes |
| ---- | ---- | ----- |
| `UniqueOperationId` | int | Game operation id |
| `PartCount` | int | Always `4` |
| `Layers[]` | array | 1–4 stacked layers |
| `Layers[i].Parts[]` | array | Length 4 (quadrants) |
| `Layers[i].Parts[j].Shape` | object or `""` | `MetaShapeSubPart` or empty |
| `Layers[i].Parts[j].Color` | object or `""` | `MetaShapeColor` or empty |
| `Id.Uid` | int | Same as operation id |
| `Hash` | string | Encoded shape+color per layer (`:` separated) |
| `$type` | string | `ShapeDefinition` / `ShapeItem` |

## Arrays detected

- Root: 70 elements
- `Layers[]`: 1–4 per recipe
- `Parts[]`: 4 per layer

## Candidate IDs

| Field | Role |
| ----- | ---- |
| `Hash` | **Canonical business key** for planner/solver (e.g. asteroid `T` field) |
| `UniqueOperationId` / `Id.Uid` | **Canonical numeric id** (unique) |
| `stable_id` | **Not usable** as unique PK |
| `MetaShapeSubPart.name` | FK to `shape_component_kind` lookup |
| `MetaShapeColor.name` | FK to `fluid_color.color_name` |
| `instance_id` | Runtime only |

## Runtime / reflection / debug strings

| Pattern | Classification |
| ------- | -------------- |
| `source_type_name` / `$type`: `ShapeItem`, `ShapeDefinition` | source metadata |
| `$unity`: `MetaShapeSubPart`, `MetaShapeColor` | source metadata |
| `instance_id` on Shape/Color | runtime metadata |

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `fluids.json` | `Color.name` values ⊆ fluid palette (9 colors) |
| `shape_catalog.py` | `SHAPE_KINDS`, `COLOR_KINDS` letter codes align with `Hash` tokens |
| `shapes.json` | 1170 entries; textual overlap with item `Hash` TBD |
| `asteroid_lab` tests | Use internal variant strings in layout, not item `Hash` directly |

## Design implication

Normalize to **`shape_recipe`** + **`shape_recipe_layer`** + **`shape_quadrant_slot`** — not 708 flat dump rows as one table without structure. Do not use `ShapeItem` as model name. Key recipes by **`shape_hash`** and/or **`operation_uid`**, not duplicate `stable_id`.
