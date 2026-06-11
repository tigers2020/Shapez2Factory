# Cross-Reference Analysis — `buildings.json`

## FK relationships (resolved)

| From | To | Cardinality | Evidence |
| ---- | -- | ----------- | -------- |
| `building.group_key` | `building_groups.json` `source_guid` | 67 : 1 | Same guid set |
| `building.snapshot_content_hash` | `building_groups` snapshot | 67 : 1 | Byte-equal JSON |
| `building_group_member.internal_variant_name` | `building_variant` | 97 : 1 | Named embeds |
| `building_group_member` (cycle) | `building_variant` (mirrored) | 34 : 1 | Inferred pairing |
| `building_simulation_setting.building_id` | `building` | 1 : 1 | |

## Parallel registries (different hashes)

| Registry | `stable_id` namespace |
| -------- | --------------------- |
| `buildings.json` | Buildings import batch |
| `building_groups.json` | Groups import batch (67 distinct hashes) |

**Never** merge hashes without proof.

## M2M (via membership)

```text
building
  └─ M2M → building_variant (through building_group_member, ordered)
```

## Ordered children

```text
building
  ├─ has one → building_simulation_setting
  ├─ has many → building_group_member (Definitions[] order)
  └─ has many → building_placement_rule
```

## Unresolved references

| Reference | Status |
| --------- | ------ |
| `translations.json` | Incomplete — LazyText in groups file not resolved here |
| `simulation_systems.json` by `source_guid` | 0 hits — uses transport_kind |
| `PipetteOverrideId` non-empty | Rare |
| `RequiredStoreContentId` | No store table in bundle |

## Diagram

```text
game_data_import_batch
  └─ has many → building (67)
        ├─ has one → building_simulation_setting
        ├─ has many → building_group_member (131)
        │     └─ references → building_variant (131 in variants file)
        │           └─ has many → building_connector
        └─ has many → building_placement_rule

building_localization_overlay (building_groups.json)
  └─ extends → building (same group_key)

research_unlock
  └─ (text) → building.group_key

toolbar_entry
  └─ (text) → building.group_key / variant titles

transport_building_registry
  └─ indirect → building_variant (not building.group_key)
```

## Cardinality

| Metric | Value |
| ------ | ----- |
| Buildings | 67 |
| Members | 131 |
| Transport buildings | 12 |
| Placement rules (total rows) | 17 |
