# Import Pipeline — `materials.json`

**Prerequisites:** `manifest.json` imported → `game_data_import_batch` + artifact checksum verified.

**Order:** Import **`materials.json` before `asset_references.json`** (meta refs FK to content `stable_id`).

## Stages

### 1. Load JSON

- Read `documents/game_data/materials.json`.
- Verify SHA-256 against `manifest.file_hashes.materials.json`.

### 2. Validate structure

- Root is array length **4**.
- Each element has required keys: `stable_id`, `material_path`, `source_path`, `display_name_key`, `source_type_name`, `source_guid`.
- `stable_id` and `material_path` unique across file.

### 3. Normalize keys and scalar values

- Trim strings; store empty `source_guid` as NULL.
- Assert `material_path == source_path` (warn if diverge in future dumps).

### 4. Register source object metadata

- Optional `source_object_record` per index `i` for audit.

### 5. Randomly sample 2–3 groups for report evidence

- Seed `20260521`; indices `0`, `1`, `2` logged in audit.

### 6. Extract canonical DTOs

```text
MaterialAssetDTO(stable_id, material_path, logical_path, display_name_key,
                 dump_source_type, unity_source_guid, source_row_index)
```

### 7. Validate DTOs

- 4 rows; enum of known `material_path` values (or allow extensibility with warning).
- Hex length 64 for `stable_id`.

### 8. Upsert root entities by canonical ID

- `material_asset` ON CONFLICT (`stable_id`) UPDATE scalars.
- Secondary UNIQUE on `material_path`.

### 9. Upsert child entities

- None (no nested children).

### 10. Resolve FK and M2M references

- After `asset_references` import: verify 4 material meta rows reference existing `stable_id`.

### 11. Validate invariants

- Count = 4.
- All `asset_meta_reference` material kind `content_stable_id` exist.
- No orphan meta material refs.

### 12. Write import audit summary

- Row count, paths list, manifest hash, sample indices.

## Idempotency

- Natural keys: `stable_id`, `material_path`.
- Re-import produces identical 4 rows and checksum.

## Unknown fields

- Route to `unknown_property`; never extend `material_asset` with JSONField blob.

## Runtime metadata

- `dump_source_type` scalar column only; no DLL/type tables.
