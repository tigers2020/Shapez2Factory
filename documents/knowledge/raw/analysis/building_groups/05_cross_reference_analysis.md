# Cross-Reference Analysis — `building_groups.json`

## FK relationships (resolved)

| From | To | Cardinality | Evidence |
| ---- | -- | ----------- | -------- |
| `building_group.group_key` | `buildings.json` `source_guid` | 67 : 1 | Same guid set |
| `building_group.snapshot_content_hash` | `building` row snapshot | 67 : 1 | 67/67 JSON equal |
| `building_group_member.internal_variant_name` | `building_variant.internal_name` | 97 : 1 | Named embedded members |
| `building_group_member.building_group_id` | `building_group` | N : 1 | 131 members / 67 groups |
| `building_group_simulation_setting.building_group_id` | `building_group` | 1 : 1 | |

## Parallel ID namespaces (intentional)

| ID | Namespace | Overlap |
| -- | --------- | ------- |
| `building_group.registry_stable_id` | `building_groups.json` | 0 with `buildings.stable_id` |
| `buildings.stable_id` | `buildings.json` | Same snapshot, different hash |
| `building_variant.stable_id` | `building_variants.json` | Embedded defs may differ in hash from variant file row |

## M2M relationships

**Logical M2M:** `building_group` ↔ `building_variant` via `building_group_member` (ordered).

Not a symmetric M2M: variants belong to exactly one group in this dump (membership is per group list).

## Ordered child relationships

```text
building_group
  ├─ has one → building_group_simulation_setting
  ├─ has one → building_group_localization_ref
  ├─ has many → building_group_member (Definitions[] order)
  │     └─ references → building_variant
  │           └─ has many → building_connector
  └─ has many → building_placement_rule (PlacementRequirements[] order)
```

## `$cycle` member resolution (intra-group)

```text
building_group (e.g. BeltDefaultVariant)
  └─ Definitions[0] embedded → BeltDefaultForwardInternalVariant
  └─ Definitions[1] embedded → BeltDefaultBackwardInternalVariant (example)
  └─ Definitions[2] {"$cycle": "..."} → points to prior embedded node
```

34 members are cycle-only placeholders; importer must resolve to variant FK without creating orphan rows.

## Unresolved / partial references

| Reference | Status |
| --------- | ------ |
| `translations.json` for LazyText keys | **Unresolved** (manifest: translations incomplete) |
| `PipetteOverrideId.Id` (non-empty) | Rare; target table TBD |
| `RequiredStoreContentId` | Present in snapshot — **review** |
| `Icon.$unity.instance_id` | Engine runtime — not FK |
| `research_unlocks.json` | Textual presence 67/67 — FK schema TBD |
| `toolbar_entries.json` | 57/67 textual hits — placement toolbar linkage TBD |

## Source metadata references

| Signal | Role |
| ------ | ---- |
| `source_type_name: BuildingDefinitionGroup` | Dump label |
| 152 `$type` strings | Serializer discriminators |
| `$unity` icons | Audit |
| `LazyText[...]` | Localization indirection |

## Relationship diagram

```text
game_data_import_batch
  └─ has many → building_group (67)
        ├─ dedupes snapshot → building (67 via buildings.json)
        ├─ has one → building_group_simulation_setting
        ├─ has one → building_group_localization_ref
        ├─ has many → building_group_member (131)
        │     └─ references → building_variant (97 embedded + 34 cycle-resolved)
        │           └─ has many → building_connector
        └─ has many → building_placement_rule (sparse)

research_unlock
  └─ (textual) references → building_group.group_key

toolbar_entry
  └─ (textual) references → building_group / variant titles

belts_pipes_transport
  └─ no direct stable_id link (transport_kind ≠ group_key)
```

## Cardinality proof

| Metric | Value |
| ------ | ----- |
| Groups | 67 |
| Unique `source_guid` | 67 |
| Unique `registry_stable_id` | 67 |
| Total `Definitions` entries | 131 |
| Named embedded variants | 97 |
| Cycle-only members | 34 |
| `building_variants.json` rows | 131 |
