# Import Pipeline Plan — `belts_pipes_transport.json`

**Prerequisites:** `building_variants.json` imported (or import both in one job with snapshot dedupe). `manifest.json` loaded for hashes.

---

## Stages

### 1. Load JSON

- Read UTF-8-sig `belts_pipes_transport.json` → `list[dict]` length 9.
- Load `building_variants.json` for dedupe validation.

### 2. Validate structure

| Rule | On failure |
| ---- | ---------- |
| 9 elements | Hard fail if count drift (manifest versioned) |
| Required envelope keys (7) | Hard fail |
| `stable_id` / variant name format | Hard fail |
| `transport_kind` unique | Hard fail |
| `definition_snapshot.Id.Name` present | Hard fail |
| Snapshot equals variant snapshot (sorted JSON hash) | Hard fail (data drift) |
| Extra keys | → `unknown_property` |

### 3. Normalize keys and scalar values

- Map `transport_kind` → `TransportKind` enum.
- Derive `transport_category` from lookup table.
- Rename: `source_guid` → `player_facing_key` in DTO.
- Strip keys containing `k__BackingField` and generic `IEntityConnectorData<...>` branches before variant parse (if parsing snapshot here).
- Map connector `$type` → `connector_role` enum.

### 4. Register source object metadata

- `game_data_import_batch` with `file_hash` for `belts_pipes_transport.json`.
- Record `source_type_name` constant and `source_method` from manifest.

### 5. Random sample for report evidence

- Seed `20260521`, indices `[1, 3, 6]` logged in audit (non-functional).

### 6. Extract canonical DTOs

```python
@dataclass(frozen=True)
class TransportBuildingRegistryDTO:
    stable_id: str
    transport_kind: str
    transport_category: str
    display_name_key: str
    player_facing_key: str
    internal_variant_name: str
    snapshot_content_hash: str
    source_row_index: int
```

Variant/connector DTOs extracted **from variant source** (preferred) or once from transport snapshot after dedupe check.

### 7. Validate DTOs

- `internal_variant_name` exists in `building_variant` table
- `snapshot_content_hash` matches stored variant hash
- `transport_kind` not empty; `stable_id` 64-hex
- Connector ordinals contiguous per variant

### 8. Upsert root entities by canonical ID

1. Upsert `building_variant` (if not exists) — **skip snapshot body if hash already present**
2. Upsert `transport_building_registry` on `stable_id`

### 9. Upsert child entities

Only when variant hash is new or connectors missing:

- `building_connector` on `(building_variant_id, ordinal)`
- `building_footprint_tile` on `(building_variant_id, ordinal)`

**Do not** re-upsert children from transport file if variant import already processed same hash.

### 10. Resolve FK and M2M references

- Resolve `building_variant_id` via `internal_name`.
- Optional: link to `buildings.json` transport groups via manual crosswalk table (future).

### 11. Validate invariants

| Invariant | Expected |
| --------- | -------- |
| Registry rows | 9 |
| Unique `transport_kind` | 9 |
| Variant FK resolved | 9/9 |
| Snapshot dedupe | 9/9 hashes match variants file |
| Orphan connectors | 0 |
| No domain JSONField blobs | 0 on registry |

### 12. Write import audit summary

```json
{
  "file": "belts_pipes_transport.json",
  "rows_upserted": 9,
  "variants_linked": 9,
  "snapshot_deduped": true,
  "connectors_skipped_duplicate": true,
  "orphan_variant_fk": 0,
  "unknown_properties": 0
}
```

---

## Idempotency

| Key | Behavior |
| --- | -------- |
| `transport_building_registry.stable_id` | Upsert scalars |
| `building_variant.internal_name` | Single canonical variant row |
| `snapshot_content_hash` | Skip child re-parse if unchanged |
| `source_row_index` | Stable per batch |

---

## Unknown / runtime handling

- Unexpected envelope keys → `unknown_property`
- `$type`, backing fields, generic interface keys → never written to domain columns raw
- `LegacyBuildingIOMap` / `$cycle` → audit attachment or ignore until spec'd

---

## Suggested command order

```text
import_building_variants
import_transport_building_registry  # depends on variants
import_building_connectors            # no-op if deduped
```
