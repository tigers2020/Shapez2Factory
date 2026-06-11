# File Inventory — `shapes.json`

## Source artifact

| Property | Value |
| -------- | ----- |
| File path | `documents/game_data/shapes.json` |
| File name | `shapes.json` |
| File size | **~1,727,753 bytes** |
| Manifest hash | `sha256:bee0de2e13dfad3c0d3b098b9538116173389f4359873ec33c2ce4a12e9f3ddf` |
| Dump context | `manifest.json` → `runtime_reflection`, v2 export |

## Top-level structure

| Property | Value |
| -------- | ----- |
| Top-level type | **array** |
| Element count | **1,170** |
| Envelope | `stable_id`, `source_*`, `display_name_key`, `definition_snapshot`, `simulation_parameters` |

## Schema difference vs `items.json`

| Aspect | `shapes.json` | `items.json` (70 rows) |
| ------ | ------------- | ---------------------- |
| Snapshot wrapper | `definition_snapshot` **is** the definition (no inner `Definition` key) | `definition_snapshot.Definition` |
| `source_type_name` | `ShapeDefinition` (1170/1170) | `ShapeItem` |
| `stable_id` | **1170 unique** | **1 repeated** (non-unique) |
| `display_name_key` | `#1` … `#1170` | constant `ShapeItem` |
| Coverage | Full catalog | Subset used in gameplay dump |

## `definition_snapshot` fields (every row)

| Field | Notes |
| ----- | ----- |
| `UniqueOperationId` | int, **1170 unique**, range 1–1330 (160 gaps) |
| `PartCount` | **4** on all rows |
| `Layers[]` | 1–4 layers |
| `Layers[].Parts[]` | 4 quadrants per layer |
| `Parts[].Shape` | `MetaShapeSubPart` or `""` |
| `Parts[].Color` | `MetaShapeColor` or `""` |
| `Hash` | **1170 unique** shape-code strings |
| `Id.Uid` | matches `UniqueOperationId` |
| `$type` | `ShapeDefinition` / serializer metadata |

## Major object groups

| Group | Count |
| ----- | ----- |
| Shape recipes | 1,170 |
| Quadrant slots (total) | ~11,000+ part records (4 × layers × recipes) |

## Layer distribution

| Layers per recipe | Count (approx.) |
| ----------------- | --------------- |
| 1 | ~500+ |
| 2–4 | remainder (same pattern as items) |

## Candidate IDs

| Field | Canonical use |
| ----- | ------------- |
| `Hash` | **Primary business key** (planner / research costs) |
| `UniqueOperationId` / `Id.Uid` | **Numeric canonical id** |
| `stable_id` | Unique in this file — audit + import correlation |
| `display_name_key` (`#N`) | **Not domain** — dump row label |

## Runtime / reflection / debug

- `$type`, `$unity`, `instance_id` on Shape/Color parts
- `ShapeDefinition` as `source_type_name` — metadata, not table name

## Cross-file references

| File | Relationship |
| ---- | ------------ |
| `items.json` | **70/70** `Hash` values ⊆ shapes (**subset**) |
| `research_unlocks.json` | **253** `ShapeHash` values ⊆ shapes (**resolved**) |
| `fluids.json` | `Color.name` palette |
| `shape_catalog.py` | Letter codes for hash tokens |

## Design implication

Use the same normalized model as `items.json`: **`shape_recipe`** + **`shape_recipe_layer`** + **`shape_quadrant_slot`**. Treat `shapes.json` as **authoritative full catalog**; `items.json` as optional gameplay subset. Do not duplicate 1,170 rows as JSONField or `ShapeDefinition` tables.
