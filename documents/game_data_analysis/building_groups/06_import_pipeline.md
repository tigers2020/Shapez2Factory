# Import Pipeline Plan — `building_groups.json`

**Prerequisites:** `buildings.json` and `building_variants.json` loaded (or single job with hash dedupe). Groups file must not inflate storage.

---

## Stages

### 1. Load JSON

- UTF-8-sig parse → list length **67**.
- Load `buildings.json` for snapshot equality checks.
- Load `manifest.json` hash.

### 2. Validate structure

| Rule | Failure |
| ---- | ------- |
| 67 elements | Hard fail if count changes |
| Required envelope keys (8) | Hard fail |
| `source_type_name == BuildingDefinitionGroup` | Warn on drift |
| `source_guid == definition_snapshot.Id.Id` | Hard fail |
| `definition_snapshot` equals buildings row (sorted JSON hash) | Hard fail on drift |
| Extra keys | → `unknown_property` |

### 3. Normalize keys and scalar values

- Parse `LazyText[building-variant.{key}.title]` → `title_key`.
- Strip `simulation_parameters` keys containing `k__BackingField`.
- Map `DefaultPreferredPlacementMode` → enum.
- Map `PlacementRequirements[].$type` → `placement_rule_kind`.
- Map connector `$type` → `connector_role` (when importing embedded defs).

### 4. Register source object metadata

- `game_data_import_batch` + `file_hashes["building_groups.json"]`.

### 5. Random sample for audit

- Seed `20260521`, indices `[8, 51, 57]` logged (non-functional).

### 6. Extract canonical DTOs

```python
@dataclass(frozen=True)
class BuildingGroupRegistryDTO:
    registry_stable_id: str
    group_key: str
    snapshot_content_hash: str
    placement_mode: str
    is_transport_building: bool
    title_key: str
    description_key: str
    simulation: BuildingGroupSimulationDTO
    source_row_index: int

@dataclass(frozen=True)
class BuildingGroupMemberDTO:
    group_key: str
    ordinal: int
    member_resolution: str  # embedded | cycle_ref
    internal_variant_name: str | None
    cycle_label: str | None
```

### 7. Validate DTOs

- `group_key` unique
- Snapshot hash matches `buildings` importer cache
- Each `internal_variant_name` exists in `building_variant` table
- Cycle members: resolver returns variant FK or hard fail
- `Definitions` length matches member DTO count

### 8. Upsert root entities by canonical ID

1. Upsert `building` / canonical snapshot from `buildings.json` (if not exists).
2. Upsert `building_group` on `group_key` (or `registry_stable_id` per policy).
3. Upsert `building_group_simulation_setting` + `building_group_localization_ref`.

### 9. Upsert child entities

- `building_group_member` on `(building_group_id, ordinal)`.
- `building_placement_rule` on `(building_group_id, ordinal)`.
- **Skip** re-importing variant geometry if `building_variant` already has same `internal_name` hash.

### 10. Resolve FK and M2M references

- `building_group.building_canonical_id` → buildings import row.
- `building_group_member.building_variant_id` → variant by `internal_name`.
- Cycle resolution: walk prior ordinals in same group matching `cycle_label` graph.

### 11. Validate invariants

| Invariant | Expected |
| --------- | -------- |
| Groups | 67 |
| Members | 131 |
| Orphan variant FK | 0 |
| Snapshot dedupe | 67/67 hashes match buildings |
| No duplicate backing-field columns | 0 |
| No domain JSONField on `building_group` | 0 |

### 12. Write import audit summary

```json
{
  "file": "building_groups.json",
  "groups_upserted": 67,
  "members_upserted": 131,
  "cycle_members": 34,
  "snapshot_matches_buildings": 67,
  "variant_fk_misses": 0,
  "unknown_properties": 0
}
```

---

## Idempotency

| Key | Behavior |
| --- | -------- |
| `group_key` | Upsert envelope scalars |
| `(building_group_id, ordinal)` | Replace member row |
| `snapshot_content_hash` | Skip canonical snapshot rewrite if unchanged |
| Variant connectors | Import once per variant `internal_name` |

---

## Import order (recommended)

```text
1. import_building_variants
2. import_buildings_canonical
3. import_building_groups_registry  # this file — envelope + members only
```

---

## Unknown / runtime handling

- Unexpected envelope keys → `unknown_property`
- `$unity`, `$cycle`, backing fields → audit strip, not domain columns
- Do not import `_Definitions` if `Definitions` present (prefer canonical array)
