# Import Pipeline Plan — `building_variants.json`

**Recommended:** Import this file **before** `building_groups.json` and `belts_pipes_transport.json` so membership and transport rows resolve variant FKs.

---

## Stages

### 1. Load JSON

- UTF-8-sig parse; expect **131** elements.
- Load manifest hash `building_variants.json`.

### 2. Validate structure

| Rule | On failure |
| ---- | ---------- |
| Count == 131 | Hard fail (versioned) |
| Envelope keys (7) | Hard fail |
| `source_guid == Id.Name` | Hard fail |
| `Id.Name` unique | Hard fail |
| `stable_id` 64-hex unique | Hard fail |
| Extra keys | `unknown_property` |

### 3. Normalize

- Map `$type` → `connector_role`.
- Map `IOType`, `TileDirection.Value`, `StandType` → enums.
- Set `is_mirrored = internal_name.endswith("Mirrored")` (review suffix rule).
- Strip keys with `k__BackingField`.
- Ignore duplicate `IEntityConnectorData<...>.AllConnectors` if `AllBuildingConnectors` present.

### 4. Register import batch

- `game_data_import_batch` + file hash.

### 5. Random sample audit

- Seed `20260521`, indices `[16, 103, 115]` logged.

### 6. Extract DTOs

```python
@dataclass(frozen=True)
class BuildingVariantDTO:
    stable_id: str
    internal_name: str
    display_name_key: str
    is_mirrored: bool
    size_x: int
    size_y: int
    size_z: int
    connector_count: int
    snapshot_content_hash: str
    source_row_index: int

@dataclass(frozen=True)
class BuildingConnectorDTO:
    internal_name: str  # parent key
    ordinal: int
    connector_role: str
    tile_direction: str
    io_channel_type: str
    ...
```

### 7. Validate DTOs

- `connector_count` matches len(connectors) unless `LabelDefaultInternalVariant` exception (document)
- Footprint tiles within `TileDimensions` bounds (optional geometry check)
- No orphan enum values

### 8. Upsert root by canonical ID

- Upsert `building_variant` on `internal_name` (or `stable_id` per policy).

### 9. Upsert children

- `building_connector` on `(building_variant_id, ordinal)`.
- `building_footprint_tile` on `(building_variant_id, ordinal)` or coordinate unique key.
- Replace children on snapshot hash change.

### 10. Resolve FKs

- Leave `building_group_id` null until `building_group_member` import fills it (optional backfill).
- Do not wait for `building_stable_id` in JSON (empty).

### 11. Validate invariants

| Check | Expected |
| ----- | -------- |
| Variants | 131 |
| Unique internal_name | 131 |
| Connectors | ≥ 0 per variant |
| Orphan connectors | 0 |
| Mirrored count | 34 |
| No JSONField on variant | 0 |

### 12. Audit summary

```json
{
  "file": "building_variants.json",
  "variants_upserted": 131,
  "connectors_upserted": 314,
  "footprint_tiles_upserted": "<count>",
  "mirrored_variants": 34,
  "zero_connector_variants": 1,
  "unknown_properties": 0
}
```

---

## Idempotency

| Key | Behavior |
| --- | -------- |
| `internal_name` | Upsert scalars |
| `(building_variant_id, ordinal)` for children | Replace on hash change |
| `snapshot_content_hash` | Skip child rewrite if unchanged |

---

## Downstream consumers

```text
import_building_variants          # this file
import_building_groups_registry   # resolves members + cycle→mirrored
import_transport_building_registry
```

When group embed snapshot differs from variant hash, **do not overwrite** variant children with partial embed.
