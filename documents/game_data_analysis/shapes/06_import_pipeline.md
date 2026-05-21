# Import Pipeline — `shapes.json`

**Prerequisites:** `manifest.json`; **`fluids.json`** → `fluid_color`; component kind seed.

**Authority:** Prefer importing **`shapes.json` as full catalog** before or instead of `items.json` (superset).

## Stages

1. Load + verify manifest hash `bee0de2e…`.
2. Validate 1170 rows; required snapshot fields; unique `Hash` and `UniqueOperationId`.
3. Normalize: empty `Shape`/`Color` → empty flags; strip `instance_id` from domain.
4. `source_object_record` per index (optional).
5. Sample indices 131, 831, 927 (seed 20260521).
6. DTO: `ShapeRecipeDTO` from `definition_snapshot` (no `Definition` wrapper).
7. Validate: fluid colors ∈ palette; 4 parts per layer; `len(Layers) == Hash.count(':')+1`.
8. Upsert `shape_recipe` on `operation_uid` / `shape_hash`.
9. Upsert layers and quadrant slots by parent + indices.
10. Resolve FKs to `fluid_color`, `shape_component_kind`.
11. Invariants: 1170 recipes; all research ShapeHash exist; 70 item hashes exist.
12. Audit: subset counts, sample hashes, checksum.

## Idempotency

Keys: `operation_uid`, (`recipe_id`, `layer_index`), (`layer_id`, `quadrant_index`).

## Dual-path importer

Support both JSON shapes:

- `definition_snapshot.Hash` (shapes.json)
- `definition_snapshot.Definition.Hash` (items.json)
