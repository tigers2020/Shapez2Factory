# Import Pipeline — `items.json`

## Prerequisites

- `fluids.json` → `fluid_color` rows
- `shape_component_kind` seeded from distinct `Shape.name` in items (or shared seed migration)

## Stages

### 1. Load JSON

- Read `documents/game_data/items.json` (UTF-8-SIG tolerant).
- Verify manifest `sha256` if `manifest.json` present.

### 2. Validate structure

- Root is array length 70.
- Each element has `definition_snapshot.Definition`.
- `PartCount == 4`; each `Layers[L].Parts` length == 4.
- `UniqueOperationId` unique; `Hash` unique.
- `len(Layers)` equals `Hash.count(':') + 1`.

### 3. Normalize keys and scalar values

- Trim strings; treat `""` Shape/Color as empty slots.
- Reject duplicate `operation_uid` / `shape_hash` within file.

### 4. Register source object metadata

- Upsert `source_object_record` per array index `i`.
- Store envelope fields; flag duplicate `stable_id` in audit note.

### 5. Randomly sample 2–3 groups for report evidence

- Seed `20260521`; indices `8`, `51`, `57` (documented in `01_sampled_objects.md`).
- Log sample hashes in import audit (non-mutating).

### 6. Extract canonical DTOs

```text
ShapeRecipeDTO(operation_uid, shape_hash, quadrant_count, layer_count)
ShapeRecipeLayerDTO(recipe_key, layer_index, hash_segment?)
ShapeQuadrantSlotDTO(recipe_key, layer_index, quadrant_index,
                     component_key?, color_name?, is_empty_shape, is_empty_color)
```

- `recipe_key` = `operation_uid` (not `stable_id`).

### 7. Validate DTOs

- Enum: `Shape.name` ∈ known component set.
- Enum: `Color.name` ∈ fluid palette or empty.
- Quadrant indices 0–3 only.

### 8. Upsert root entities by canonical ID

- `shape_recipe` ON CONFLICT (`operation_uid`) UPDATE `shape_hash`, counts.
- Secondary unique on `shape_hash`.

### 9. Upsert child entities by parent canonical ID + order/index/key

- Delete-replace or upsert layers: (`shape_recipe_id`, `layer_index`).
- Upsert slots: (`shape_recipe_layer_id`, `quadrant_index`).
- Preserve `layer_index` / `quadrant_index` ordering.

### 10. Resolve FK and M2M references

- Lookup `shape_component_kind_id` by `component_key`.
- Lookup `fluid_color_id` by `color_name`.
- Null FKs when empty shape/color.

### 11. Validate invariants

- 70 recipes; slot count = sum over recipes of `4 * layer_count`.
- No orphan slots.
- Optional: recompute hash from slots and compare to `shape_hash`.

### 12. Write import audit summary

- Counts: recipes, layers, slots, empty slots, unknown properties.
- Manifest hash, file checksum, seed samples.
- Warnings: duplicate `stable_id`, hash mismatch.

## Idempotency

| Rule | Guarantee |
| ---- | --------- |
| Natural keys | `operation_uid`, (`recipe_id`, `layer_index`), (`layer_id`, `quadrant_index`) |
| Re-run | Same row counts and FK graph |
| Checksum | Deterministic hash over canonical DTO serialization (sorted keys) |

## Unknown fields

- Route to `unknown_property` linked to `source_object_record`.
- Never merge into `shape_recipe` JSON columns.

## Runtime metadata

- `instance_id`, `$type`, `$unity` → audit JSON on `source_object_record` only if retained.
