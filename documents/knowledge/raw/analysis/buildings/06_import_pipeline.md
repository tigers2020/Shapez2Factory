# Import Pipeline Plan — `buildings.json`

**Prerequisites:** `building_variants.json` imported first (131 rows). Optional: `building_groups.json` for localization overlay only.

---

## Stages 1–12

### 1. Load JSON

- Parse 67 elements; manifest hash `buildings.json`.

### 2. Validate structure

| Rule | Failure |
| ---- | ------- |
| Count == 67 | Hard fail |
| Required envelope keys (7) | Hard fail |
| `source_guid == Id.Id == display_name_key` | Hard fail |
| `Definitions` total slots == 131 | Hard fail |
| Extra keys | `unknown_property` |

### 3. Normalize

- Strip `simulation_parameters` backing fields.
- Map placement mode + placement rule `$type` → enums.
- Parse member `Id.Name` / `$cycle`.

### 4. Register batch

- `game_data_import_batch` with file hash.

### 5. Random sample audit

- Seed `20260521`, indices `[8, 51, 57]` logged.

### 6. DTOs

```python
@dataclass(frozen=True)
class BuildingDTO:
    stable_id: str
    group_key: str
    display_name_key: str
    is_transport_building: bool
    placement_mode: str
    snapshot_content_hash: str
    source_row_index: int
```

### 7. Validate DTOs

- Variant FK for all named members.
- Cycle members resolvable (34).
- Snapshot hash stable.

### 8. Upsert roots

- `building` on `group_key` (or `stable_id`).
- `building_simulation_setting` 1:1.

### 9. Upsert children

- `building_group_member` by `(building_id, ordinal)`.
- `building_placement_rule` by `(building_id, ordinal)`.
- **Do not** re-import variant connectors from embed if variant file already imported.

### 10. Resolve FKs

- `building_variant_id` from `internal_name`.
- Optional overlay from `building_groups.json` → `building_localization_overlay`.

### 11. Invariants

| Check | Expected |
| ----- | -------- |
| Buildings | 67 |
| Members | 131 |
| Orphan variant FK | 0 |
| Transport count | 12 |

### 12. Audit

```json
{
  "file": "buildings.json",
  "buildings_upserted": 67,
  "members_upserted": 131,
  "cycle_members": 34,
  "transport_buildings": 12
}
```

---

## Idempotency

Upsert on `group_key`; replace ordered children; `snapshot_content_hash` gates snapshot-derived reparse.

---

## Recommended order

```text
import_building_variants
import_buildings              # this file
import_building_groups_i18n   # optional overlay only
import_transport_registry
```

When `building_groups.json` snapshot matches, **skip** rewriting `building` snapshot fields from second file.
